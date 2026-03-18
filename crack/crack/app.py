# pip install flask
import hashlib
import os


import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymysql import cursors
from pymysql.cursors import DictCursor
from ultralytics import YOLO

from common.Session import Session # crack. 제거
from domain import Member # crack. 제거
from service import MemberService # crack. 제거

# 1. 경로 문제 해결을 위해 현재 파일의 절대 경로를 기준으로 설정합니다.
# base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'its_guard'
# app.secret.key 에 its_guard라고 해놓은 이유
# session 데이터 암호화
# 데이터 위조 방지 (쿠키 보안)
# 사용자 메시지 출력.

model = YOLO(r'C:\Users\lsh8389\Desktop\ITS-Guard_Project\best.pt')

UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_conn()
    try:
        with conn.cursor() as cursor:
            # 1. 회원 정보 조회
            sql = "SELECT id, name, uid, role  FROM members WHERE uid = %s AND password = %s"
            cursor.execute(sql, (uid, upw))
            user = cursor.fetchone()

            if user:
                # 2. 로그인 성공: 세션에 사용자 정보 저장
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_uid'] = user['uid']
                session['user_role'] = user['role']

                # 이제 DB에서 'role'을 가져왔으니 에러 없이 잘 들어갈 겁니다.
                # session['user_role'] = user['role']

                return redirect(url_for('index'))
            else:
                return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.'); history.back();</script>"
    finally:
        conn.close()


@app.route('/admin/dashboard')
def admin_dashboard():
    # 보안 : 관리자가 아니면 홈으로 튕겨내기
    if session.get('user_id') != 'admin':
        return "<script>alert('관리자 전용 페이지 입니다.'); history.back();</script>"

    conn = Session.get_conn()
    try:
        with conn.cursor(pymysql, cursors, DictCursor) as cursor:
            # 모든 사용자의 제보 내역을 가져옵니다.
            sql = """
                    SELECT p.*, m.name as reporter_name
                    FROM potholes p
                    JOIN members m ON p.reporter_id = m.id
                    ORDER BY p.created_at DESC
            """
            cursor.execute(sql)
            all_reports = cursor.fetchall()

            return render_template('admin_dashboard.html', reports=all_reports)
    finally:
        conn.close()

# 2. 제보 상태 변경 (검토중 -> 완료 및 포인트 지급)
@app.route('/admin/update_status/<int:report_id>', methods=['POST'])
def update_status(report_id):
    if session.get('user_id') != 'admin':
        return redirect(url_for('index'))

    new_status = request.form.get('status') # 완료 또는 반려

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # 상태 업데이트
            sql = "UPDATE potholes SET status = %s WHERE id = %s"
            cur.execute(sql, (new_status, report_id))
            conn.commit()

            return f"<script>alert('상태가 {new_status}로 변경되었습니다.');location.href='/admin/dashboard';</script>"
    finally:
        conn.close()

@app.route('/update_report_status', methods=['POST']) # 서비스 사용자가 제보한 도로 파손(포트홀), 사건의 처리 상태를 업데이트하는
# 뒷단 백엔드로직. 예를들어, 대기 중인 제보를 확인 완료상태로 바꿀 때 실행되는 기능.
# 상태를 수정 하는 것이므로 보안상 POST 방식 사용
def update_report_status():
    data = request.get_json()
    # 프론트엔드(자바스크립트) 에서 보낸 JSON 데이터를 파이썬 딕셔너리 형태로 변환해서 가져옴.
    report_id = data.get('id')
    # 보내온 데이터 중 어떤 제보물을 어떤 상태로 바꿀지 변수에 저장함.
    new_status = data.get('status')

    db = Session.get_conn()

    # try: 일단이 코드를 실행해
    # except: 만약 에러가 나면 rollback() 을 통해서 데이터를 원래대로 복구
    # finally: 성공하든 실패하든 마지막엔 반드시 DB 연결을 닫아서 자원 낭비를 줄임
    try:
        # DB 연결 및 업데이트 (MySQL 예시)
        with db.cursor() as cursor:
            cursor = db.cursor()
            sql = "UPDATE reports SET status = %s WHERE id = %s"
            cursor.execute(sql, (new_status, report_id))
            # 실제 MySQL에 보낼 명려문. reports 테이블에서 특정 id를 찾아서 상태를 업데이트하라고 시키는 핵심코드

            if new_status == '처리완료':
                # 해당 제보를 작성한 유저를 찾아서 포인트를 10점 올리는 쿼리
                # reports 테이블에 user_id가 저장되어 있다는 가정하에 작성된 서브쿼리문
                point_sql = """
                                    UPDATE users
                                    SET point = point + 10
                                    WHERE user_id = (SELECT user_id FROM reports WHERE id = %s)
                """
                cursor.execute(point_sql, (report_id,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message":str(e)})
    finally:
        db.close()

@app.route('/report') # 제보를 할 수 있는 기능. 주소창 https://192.168.0.157:5001/report
def report_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('report.html') # report.html 파일을 불러옴.


@app.route('/report/submit', methods=['POST'])
def report_submit():
    # 1. 로그인 확인
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.'); location.href='/login';</script>"

    # 2. HTML 폼에서 데이터 가져오기
    user_uid = session.get('user_uid')
    address = request.form.get('address')
    severity = request.form.get('severity')
    lat = request.form.get('lat') or 37.283  # 좌표가 없으면 기본값
    lng = request.form.get('lng') or 127.045

    # 3. DB 접속 및 저장
    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # potholes 테이블에 제보 정보 저장
            sql = """INSERT INTO potholes 
                     (address, severity, lat, lng, reporter_id, status, points) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cur.execute(sql, (address, severity, lat, lng, user_uid, '검토중', 10))
            conn.commit()

        return f"""
            <script>
                alert('도로 파손 제보가 성공적으로 접수되었습니다!');
                location.href = "/mypage";
            </script>
        """
    except Exception as e:
        print(f"제보 저장 에러: {e}")
        return f"<script>alert('저장 중 오류가 발생했습니다.'); history.back();</script>"
    finally:
        conn.close()

@app.route('/report/quick', methods=['POST'])
def quick_report():
    """
    지도(좌표) 없이 버튼 클릭만으로 즉시 제보와 포인트를 지급하는 로직
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_uid = session.get('user_uid')
    # 사용자가 선택한 제보 유형 (예: 포트홀, 파손 등)을 받아옵니다.
    severity = request.form.get('severity')

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # 1. 제보 내역 저장 (지도 정보 없이 기본 데이터만 입력)
            # 상태는 '검토중'으로 설정하고, 즉시 10포인트를 부여합니다.
            sql = """
                        INSERT INTO potholes (reporter_id, severity, status, points)
                        VALUES (%s, %s, %s, %s)
            """
            # 2. (선택사항) members 테이블에 포인트 합계를 별도로 관리한다면 아래 쿼리 실행
            # sql_member = "UPDATE members SET points = points + 10 WHERE uid = %s"
            # cur.execute(sql,_member, (user_uid,))

            conn.commit()
            return "<script>alert('제보가 완료되었습니다. 10포인트가 적립됩니다.');location.href='/';</script>"
    except Exception as e:
        conn.rollback()
        print(f" 제보 에러 : {e}")
        return f"<script>alert('처리 중 오류가 발생했습니다.');history.back();</script>"
    finally:
        conn.close()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')

    uid = request.form.get('uid')
    password = request.form.get('password')
    password_check = request.form.get('password_check')# 컬럼명 password에 맞춤
    name = request.form.get('name')

    # 1.  비밀번호 일치 여부 확인
    if password != password_check:
        return "<script>alert('비밀번호가 일치하지 않습니다.');history.back();</script>"

    conn = Session.get_conn()
    try:
        with conn.cursor() as cursor:
            # 아이디 중복 확인
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

            # 회원 정보 저장 (role, active는 기본값이 들어감)
            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다!'); location.href='/login';</script>"
    except Exception as e:
        print(f"회원가입 에러: {e}")
        return "가입 중 오류가 발생했습니다."
    finally:
        conn.close()

@app.route('/check_id', methods=['POST']) # 회원가입 할 때 가입 버튼 누르기 전에, 아이디 입력후 아이디 중복확인 클릭기능추가.
def check_id():
    uid = request.json.get('uid') # 자바스크립트 fetch로 받을 때 사용
    conn = Session.get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            exists= cursor.fetchone()
            if exists:
                return jsonify({"available": False})
            return jsonify({"available": True})
    finally:
        conn.close()

@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_uid = session['user_uid']

    # 1. 페이지 기능 추가
    page = request.args.get('page', 1, type=int) # 현재 페이지 기본값 1
    per_page = 5 # 한 페이지에 보여줄 제보 (신고) 건수
    offset = (page - 1 ) * per_page

    conn = Session.get_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur: # 데이터를 딕셔너리 (key : value) 형태로 받음.
            # 1. 사용자 정보 조회
            user_sql = "SELECT id, name, uid, role, created_at FROM members WHERE uid = %s"
            cur.execute(user_sql, (user_uid,))
            user_data = cur.fetchone()

            count_sql = "SELECT COUNT(*) as cnt FROM potholes WHERE reporter_id = %s"
            cur.execute(count_sql, (user_uid,))
            total_count = cur.fetchone()['cnt']
            total_pages = (total_count + per_page - 1 ) // per_page # 반올림 계산

            # 2. 제보 내역 조회 (potholes 테이블 사용)
            report_sql = """
                SELECT id, severity as type, address, status, created_at as date
                FROM potholes
                WHERE reporter_id = %s 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cur.execute(report_sql, (user_uid, per_page, offset))
            my_reports = cur.fetchall()

            print(f"조회된 제보 건수 : {len(my_reports)}")

            # 3. 총 포인트 합산 (중복 코드 제거 및 테이블명 통일)
            sum_sql = "SELECT SUM(points) as total_points FROM potholes WHERE reporter_id = %s"
            cur.execute(sum_sql, (user_uid,))
            result = cur.fetchone()
            total_points = result['total_points'] if result and result['total_points'] else 0

            # 4. 결과 전달 (page와 total_page 추가)
            return render_template('mypage.html',
                                   user=user_data,
                                   reports=my_reports,
                                   total_points=total_points,
                                   page=page,
                                   total_pages=total_pages)

    except Exception as e:
        print(f"에러 발생: {e}")
        return f"<script>alert('오류가 발생했습니다: {e}');history.back();</script>"
    finally:
        if 'cur' in locals():
            cur.close()
        conn.close()


@app.route('/update', methods=['POST'])
def update():
    # 1. 폼 데이터 수집 (HTML의 name 속성과 일치해야 함)
    new_name = request.form.get('name')
    new_pw = request.form.get('password')

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']  # 세션에 저장된 DB 고유 번호(PK) 사용
    conn = Session.get_conn()

    try:
        with conn.cursor() as cur:
            if new_pw:  # 새 비밀번호가 입력된 경우
                # [확인됨] DB 컬럼명이 'password'이므로 아래와 같이 수정
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                cur.execute(sql, (new_name, new_pw, user_id))
            else:  # 비밀번호는 그대로 두고 이름만 변경할 경우
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cur.execute(sql, (new_name, user_id))

            conn.commit()

            # 2. 실시간 세션 정보 갱신 (화면 상단 이름 변경용)
            session['user_name'] = new_name

            return "<script>alert('성공적으로 수정되었습니다.'); location.href='/update';</script>"

    except Exception as e:
        conn.rollback()
        print(f"Update Error: {e}")
        return f"<script>alert('오류가 발생했습니다: {e}'); history.back();</script>"
    finally:
        conn.close()

@app.route('/withdraw', methods=['POST'])
def withdraw():
    pw_confirm = request.form.get('pw_confirm')

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # 비밀번호 확인 후 삭제
            sql = "DELETE FROM members WHERE id=%s AND password=%s"
            cur.execute(sql, (session['user_id'], pw_confirm))

            if cur.rowcount > 0: # 실제 삭제된 행이 있다면 성공.
                conn.commit()
                session.clear() # 세션 비우기
                return "<script>alert('그동안 이용해주셔서 감사합니다.');location.href='/';</script>"
            else:
                return "<script>alert('비밀번호가 일치하지 않습니다.');history.back();</script>"
    finally:
        conn.close()


@app.route('/update_page')  # 1. 앞에 / 추가
def update_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = Session.get_conn()
    try:
        # 2. pymysql.cursors.DictCursor (마침표 확인)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 3. password 뒤 콤마 제거
            sql = "SELECT name, uid, password FROM members WHERE id = %s"
            cur.execute(sql, (user_id,))
            user_data = cur.fetchone()

            # 4. 사용자의 제보 내역도 같이 가져와야 마이페이지가 깨지지 않습니다.
            cur.execute("SELECT * FROM potholes WHERE reporter_id = %s", (user_id,))
            my_reports = cur.fetchall()

            # 5. 포인트 합계도 가져오기
            cur.execute("SELECT SUM(points) as total_points FROM potholes WHERE reporter_id = %s", (user_id,))
            total_points = cur.fetchone()['total_points'] or 0

        # 핵심: show_edit=True 라는 신호를 보내서 HTML에서 입력창을 띄우게 합니다.
        return render_template('mypage.html',
                               user=user_data,
                               reports=my_reports,
                               total_points=total_points,
                               show_edit=True)
    except Exception as e:
        print(f"Error: {e}")
        return redirect('/mypage')
    finally:
        conn.close()

@app.route('/check_pothole', methods=['POST'])
def check_pothole():
    # 1. 로그인 여부 확인 (선택 사항 : 로그인 한 사용자에게만 알림을 줄 경우)
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "로그인이 필요합니다."}), 401

    # 2. 클라이언트 (웹 브라우저)에서 보낸 현재 위치 좌표 바딕
    data = request.json
    user_lat = data.get('lat')
    user_lng = data.get('lng')

    if not user_lat or not user_lng:
        return jsonify({"status": "error","message": "좌표 정보가 없습니다."}), 400

    conn = Session.get_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 3. ST_Distance_Sphere를 사용하여 반경 100m 내 포트홀 검색
            # 덕영대로 같은 간선도로는 차가 빠르므로 200~300m로 조절해도 괜찮음.
            sql = """
                            SELECT id, lat, lng, 
                            (6371 * acos(cos(radians(%s)) * cos(radians(lat)) * cos(radians(lng) - radians(%s)) + sin(radians(%s)) * sin(radians(lat)))) AS distance 
                            FROM potholes 
                            WHERE status = '검토중' AND detect_count > 0
                            HAVING distance < 0.1
                            ORDER BY created_at DESC LIMIT 1
            """
            # SQL 파라미터 순서에 맞춰 변수 전달 (lat, lng, lat)
            cur.execute(sql, (user_lat, user_lng, user_lat))

            # 결과를 nearby_potholes 변수에 담아서 아래 return 문과 일치
            nearby_potholes = cur.fetchall()

            return jsonify({
                "status": "success",
                "count": len(nearby_potholes),
                "data": nearby_potholes
            })

    except Exception as e:
        print(f"포트홀 조회 에러 : {e}")
        return jsonify({"status": "error", "message": "조회 중 오류 발생"}), 500

    finally:
        conn.close()

@app.route('/predict', methods=['POST']) # 사용자가 올린 영상을 AI 모델(YOLO)이 직접 분석해서
# 포트홀이 어디에 몇 개 있는지를 찾아내는 로직.
# 영상 저장 : 사용자가 올린 파일을 uploads 폴더에 저장함.
# AI 분석 : model.predict를 실행해 영상 속 포트홀을 찾고, 분석 결과 영상을 static/exp에 저장함.
# 데이터 기록 : 탐지된 개수 detect_count 결과 영상 경로, 그리고 발생 위치(위경도)를 DB potholes 테이블에 차곡차곡 쌓음.
# 결과 출력 : 분석이 끝나면 메인화면에 몇개 찾았습니다. 라고 알림창이 나옴.
def predict():
    file = request.files['video']
    if file:
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        model.predict(source=filepath, save=True, conf=0.3)

        # AI 분석 실행 (project와 name을 지정하면 경로 찾기가 쉬워짐)
        results = model.predict(source=filepath, save=True, project="static", name="exp", exist_ok=True)

        # 🌟 탐지된 개수 세기
        detect_count = len(results[0].boxes)

        # 분석된 영상의 파일명 (static/exp 폴더 안에 저장됨)
        result_video = f"exp/{file.filename}"

        # get_conn() 함수를 사용하여 DB에 기록
        conn = Session.get_conn()
        try:
            with conn.cursor() as cur:
                # 데이터를 넣는 SQL 쿼리문
                # 테스트를 위해 임시 좌표(예: 아주대 근처)
                # 실제 서비스에선 영상의 GPS 정보를 추출하거나 사용자 위치를 넣어야 함.
                test_lat, test_lng = 37.283, 127.045

                sql = """INSERT INTO potholes (filename, detect_count, result_path, lat, lng, status)
                                     VALUES (%s, %s, %s, %s, %s, %s)"""
                cur.execute(sql, (file.filename, detect_count, result_video, test_lat, test_lng, '검토중'))
                conn.commit()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cur.close()
            conn.close()

        # 화면으로 결과 전달
        return render_template("main.html",
                               results=results,
                               result_video=result_video,
                               count=detect_count)
    return "파일 없음"

#@app.route('/')
#def index():
    return '''
    <h2> 🚀 ITS-Guard 웹 서비스 </h2>
    <form action="/predict" method="post" enctype="multipart/form-data">
        <input type="file" name="video"  accept="video/mp4">
        <button type="submit"> AI 분석 시작</button>
    </form>
    '''

@app.route('/')
def index():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)