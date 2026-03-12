# pip install flask
import hashlib
import os
import re

import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymysql import cursors
from pymysql.cursors import DictCursor

from common.Session import Session # crack. 제거
from domain import Member # crack. 제거
from service import MemberService # crack. 제거

# 1. 경로 문제 해결을 위해 현재 파일의 절대 경로를 기준으로 설정합니다.
# base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'its_guard_secret_key' # 이 줄이 없으면 세션 에러가 납니다.

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
                session['user_role'] = user['role']

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

@app.route('/report') # 제보를 할 수 있는 기능. 주소창 https://192.168.0.157:5001/report
def report_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('report.html') # report.html 파일을 불러옴.

@app.route('/report/submit', methods=['POST'])
def report_submit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_uid = session.get('user_uid')
    address = request.form.get('address')
    severity = request.form.get('severity')
    lat = request.form.get('lat')
    lng = request.form.get('lng') # lon이 아닌 lng로 받기

    # 좌표가 비어있으면 뒤로 가기
    if not lat or not lng:
        return "<script>alert('좌표 데이터가 없습니다. 주소를 다시 검색해주세요.'); history.back();</script>"

    # 주소에서 지역명 추출
    region_name = None
    if address:
        if '경기도' in address: region_name = '경기도'
        elif '강원도' in address: region_name = '강원도'
        elif '충청도' in address: region_name = '충청도'

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # DB 컬럼 개수(8개)와 VALUES 개수(8개)를 정확히 맞춤
            sql = """
                INSERT INTO potholes (reporter_id, address, severity, status, points, lat, lng, region_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (user_uid, address, severity, '검토중', 10, lat, lng, region_name))
            conn.commit()
            return "<script>alert('제보가 완료되었습니다! 10포인트가 적립됩니다.'); location.href='/';</script>"
    except Exception as e:
        print(f"저장 에러: {e}")
        return f"<script>alert('저장 실패: {e}'); history.back();</script>"
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
    password = request.form.get('password')  # 컬럼명 password에 맞춤
    name = request.form.get('name')

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


@app.route('/mypage') # 관리자 모드 페이지. 주소창에 https://192.168.0.157:5001/mypage
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_uid = session['user_uid']
    conn = Session.get_conn()
    try:
        # pymysql.cursors.DictCursor 로 수정 (점 확인!)
        with conn.cursor(pymysql.cursors.DictCursor) as cur:

            # 1. [필수] 먼저 members 테이블에서 사용자 정보를 가져와야 합니다.
            user_sql = "SELECT id, name, uid, role, created_at FROM members WHERE uid = %s"
            cur.execute(user_sql, (user_uid,))
            user_data = cur.fetchone()  # 여기서 사용자 한 명의 정보가 담깁니다.

            print(f"DEBUG: DB 조회 결과 -> {user_data}")

            if not user_data:
                return f"<script>alert('사용자 정보 없음! (세션ID: {user_uid})');history.back();</script>"

            # 2. 사용자가 제보한 내용 가져오기 (potholes 테이블)
            report_sql = """
                SELECT id, address, severity, status, points, created_at 
                FROM potholes 
                WHERE reporter_id = %s 
                ORDER BY created_at DESC
            """
            cur.execute(report_sql, (user_uid,))
            my_reports = cur.fetchall()  # 여러 건이므로 fetchall

            # 3. 총 포인트 합계 계산
            sum_sql = "SELECT SUM(points) as total_points FROM potholes WHERE reporter_id = %s"
            cur.execute(sum_sql, (user_uid,))
            result = cur.fetchone()
            total_points = result['total_points'] if result and result['total_points'] else 0

            return render_template('mypage.html',
                                   user=user_data,
                                   reports=my_reports,
                                   total_points=total_points)
    except Exception as e:
        print(f"에러 발생: {e}")
        return f"<script>alert('오류가 발생했습니다: {e}');history.back();</script>"
    finally:
        conn.close()



@app.route('/update', methods=['POST'])
# 개인정보수정, 사용자가 입력한 새로운 정보를 DB에 UPDATE 하는 로직.
# 비밀번호 변경 여부에 따라서 쿼리를 나누는 것이 좋을 것 같아서 나누었음//
def update():
    new_name = request.form.get('new_name')
    new_addr = request.form.get('new_addr')
    new_pw = request.form.get('new_pw')

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            if new_pw: # 비밀번호도 변경할 경우
                sql = "UPDATE members SET naem = %s, address=%s, password=%s WHERE id=%s"
                cur.execute(sql, (new_name, new_addr, new_pw, session['user_id']))
            else: # 비밀번호는 유지 할 경우
                sql = "UPDATE members SET name=%s, address=%s WHERE id=%s"
                cur.execute(sql, (new_name, new_addr, session['user_id']))
            conn.commit()
            session['user_name'] = new_name # 세션 이름 정보도 갱신
            return "<script>alert('개인정보가 수정되었습니다.');location.href='/update';</script>"
    except Exception as e:
        conn.rollback()
        return f"<script>alert('정보 수정 중 오류 발생');history.back();</script>"
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


# Flask에서 '근처 포트홀 조회' API 생성.
# 사용자의 현재 위치 좌표(위도, 경도)를 받아서, DB내 의 포트홀 좌표들과 비교해 반경 100m 이내에 있는 것들만 반환하는 로직.
# 이 코드는 시스템의 심장부와 같은 역할을 하는 핵심 로직이에요.

@app.route('/check_pothole', methods=['POST'])
def check_pothole():
    # 1. 로그인 여부 확인 (선택 사항 : 로그인 한 사용자에게만 알림을 줄 경우)
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "로그인이 필요합니다."}), 401

    # 2. 클라이언트 (웹 브라우저)에서 보낸 현재 위치 좌표 바딕
    data = request.json
    user_lat = data.get('lat')
    user_lon = data.get('lng')

    if not user_lat or not user_lon:
        return jsonify({"status": "error","message": "좌표 정보가 없습니다."}), 400

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # 3. ST_Distance_Sphere를 사용하여 반경 100m 내 포트홀 검색
            # 덕영대로 같은 간선도로는 차가 빠르므로 200~300m로 조절해도 괜찮음.
            sql = """
                SELECT id, lat, lng, severity, address,
                       ST_Distance_Sphere(point(lng, lat), point(%s, %s)) AS distance
                FROM potholes
                HAVING distance <= 100
                ORDER BY distance ASC
            """
            cur.execute(sql, (user_lat, user_lon))
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

@app.route('/map')
def view_map():
    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # lat, lng가 있는 데이터만 가져와서 지도에 표시
            sql = "SELECT id, address, severity, lat, lng FROM potholes WHERE lat IS NOT NULL"
            cur.execute(sql)
            potholes_list = cur.fetchall()
            # 변수명을 potholes로 통일하세요!
            return render_template('map.html', potholes=potholes_list)
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)