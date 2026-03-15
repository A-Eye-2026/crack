# pip install flask
# 플라스크란?
# 파이썬으로 만든 db연동 콘솔 프로그램을 웹으로 연결하는 프레임워크
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 것
# app.py 는 플라스크로 서버를 동작하기 위한 파일명 (기본파일)
# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
# static : 정적 파일을 모아놓는 곳 (html, css, js)
# templates : 동적 파일을 모아놓는 곳 (crud 화면, 레이아웃, index 등..)

import requests
import math
import os

from flask import Flask,render_template,request,redirect,url_for,session, jsonify, send_from_directory
from common.Session import Session
from domain import *
#                플라스크    프론트 연결      요청,응답  주소전달   주소생성  상태저장

app = Flask(__name__)
app.secret_key = '1234'


from decimal import Decimal

# 주소 검색 시 도시 입력만으로도 해당 행정구 목록을 제공하기 위한 지역 데이터 사전
KAKAO_REST_API_KEY = "035c39ca6433bc71c470c3174e362005"
DEFAULT_RADIUS_M = 700
CITY_DISTRICT_MAP = {
        "수원시": ["장안구", "권선구", "팔달구", "영통구"],
        "성남시": ["수정구", "중원구", "분당구"],
        "안양시": ["만안구", "동안구"],
        "용인시": ["처인구", "기흥구", "수지구"],
        "고양시": ["덕양구", "일산동구", "일산서구"],
        "서울시": [
            "종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구",
            "성북구", "강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구",
            "양천구", "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구",
            "서초구", "강남구", "송파구", "강동구"
        ]
    }


# 두 좌표 사이 실제 거리를 계산하여 위치 기반 사건 필터링에 사용하는 함수
def haversine_m(lat1, lon1, lat2, lon2):
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    r = 6371000  # meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(current_dir, 'static', 'uploads')
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        return f"파일 없음: {file_path}", 404

    return send_from_directory(upload_folder, filename)

# 주소 검색 API
@app.route('/api/address/search')
def address_search():
    keyword = request.args.get('q', '').strip()

    if not keyword:
        return jsonify({
            'success': False,
            'message': '검색어를 입력해주세요.',
            'items': []
        }), 400

    # 도시 이름만 입력해도 전체 지역과 하위 행정구를 즉시 확장해 보여주는 검색 보완 로직
    # 시 단위 검색이면 "시 전체" + 구 목록 반환
    matched_city = None
    for city_name in CITY_DISTRICT_MAP.keys():
        if keyword == city_name or keyword == city_name.replace('시', ''):
            matched_city = city_name
            break

    if matched_city:
        items = []

        # 시 전체 보기
        items.append({
            'address_name': f"{matched_city} 전체",
            'latitude': None,
            'longitude': None,
            'is_city_district': True,
            'city': matched_city,
            'district': ''
        })

        # 구 목록
        for district in CITY_DISTRICT_MAP[matched_city]:
            items.append({
                'address_name': f"{matched_city} {district}",
                'latitude': None,
                'longitude': None,
                'is_city_district': True,
                'city': matched_city,
                'district': district
            })

        return jsonify({
            'success': True,
            'items': items
        })

    # 상세 주소 검색은 카카오 API 사용
    try:
        headers = {
            "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
        }
        params = {
            "query": keyword,
            "size": 10
        }

        resp = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers=headers,
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()

        items = []
        for doc in data.get('documents', []):
            road_addr = doc.get('road_address') or {}
            addr = doc.get('address') or {}

            address_name = (
                road_addr.get('address_name')
                or addr.get('address_name')
                or doc.get('address_name')
            )

            items.append({
                'address_name': address_name,
                'latitude': float(doc.get('y')),
                'longitude': float(doc.get('x')),
                'is_city_district': False
            })

        return jsonify({
            'success': True,
            'items': items
        })

    except Exception as e:
        print(f"주소 검색 오류: {e}")
        return jsonify({
            'success': False,
            'message': '주소 검색 중 오류가 발생했습니다.',
            'items': []
        }), 500

@app.route('/login',methods=['GET','POST'])
    # methods는 웹의 동작에 관여한다
    # GET : URL 주소로 데이터를 처리 (보안상 좋지 않음, 대신 빠름)
    # POST : BODY 영역의 데이터를 처리 (보안상 좋음, 대용량일 때 많이 사용됨)
    # 대부분 처음에 화면(HTML 랜더)을 요청할 때는 GET 방식 처리 ----- 로그인 화면 출력 할 때
    # 화면에 있는 내용을 백앤드로 전달할 때는 POST 방식 처리 ----- 로그인 정보를 데이터베이스에 확인할 때
def login():
    if request.method == 'GET':
        return render_template('login.html')
        # GET 방식으로 요청하면 login,html 화면이 나옴
    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = 'SELECT id,name,uid,role FROM members WHERE uid = %s and password = %s'
            #                                                 uid와 password가 동일한지
            #             id,name,uid,role을 가져옴
            cursor.execute(sql,(uid,upw))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_uid'] = user['uid']
                session['user_role'] = user['role']

                return redirect(url_for('index'))
            else:
                return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.');history.back();</script>"
    finally:
        conn.close()
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
@app.route('/join',methods=['GET','POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')
    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디입니다.');history.back();</script>"
            sql = "INSERT INTO members (uid,password,name) VALUES (%s,%s,%s)"
            cursor.execute(sql,(uid,password,name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다.');location.href='/login';</script>"
    except Exception as e:
        print(f"회원가입 오류 : {e}")
        return "가입 중 오류가 발생했습니다. \n join()메서드를 확인하세요."
    finally:
        conn.close()
@app.route('/member/edit',methods=['GET','POST'])
def member_edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html',user=user_info)
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw:
                sql = 'UPDATE members SET name = %s, password = %s WHERE id = %s'
                cursor.execute(sql,(new_name,new_pw,session['user_id']))
            else:
                sql = 'UPDATE members SET name = %s WHERE id = %s'
                cursor.execute(sql,(new_name,session['user_id']))

            conn.commit()
            session['user_name'] = new_name
            return "<script>alert('정보가 수정되었습니다.');location.href='/mypage';</script>"
    except Exception as e:
        print(f"회원수정 오류 : {e}")
        return "수정 중 오류가 발생했습니다. \n member_edit()메서드를 확인하세요."
    finally:
        conn.close()
@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) AS board_count FROM boards where member_id = %s', (session['user_id'],))
            board_count = cursor.fetchone()['board_count']

            return render_template('mypage.html',user=user_info,board_count=board_count)
    finally:
        conn.close()
######################################## 회원 CRUD ####################################################################

####################################### 게시판 CRUD ####################################################################
@app.route('/board/write',methods=['GET','POST']) # http://localhost:5000/board/write
def board_write():
    # 1. 사용자가 '글쓰기' 버튼을 눌러서 들어왔을 때 (화면 보여주기)
    if request.method == 'GET':
        # 로그인 체크 (로그인 안 했으면 글 못 쓰게)
        if 'user_id' not in session:
            return '<script>alert("로그인 후 이용 가능합니다.");location.href="/login";</script>'
        return render_template('board_write.html')
    elif request.method == 'POST': # <form action="/board/write" method="POST">
        title = request.form.get('title')
        content = request.form.get('content')
        # 세션에 저장된 로그인 유저의 id (member_id)
        member_id = session.get('user_id')

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'INSERT INTO boards (member_id,title,content) VALUES (%s,%s,%s)'
                cursor.execute(sql,(member_id,title,content))
                conn.commit()
            return redirect(url_for('board_list')) # 저장 후 목록으로 이동
        except Exception as e:
            print(f"글쓰기 에러 : {e}")
            return "저장 중 에러가 발생했습니다."
        finally:
            conn.close()

@app.route('/board') # http:/localhost:5000/board
def board_list():
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 작성자 이름을 함께 가져오기 위해 JOIN 사용
            sql = """
            SELECT b.*, m.name as writer_name
            FROM boards b
            JOIN members m ON b.member_id = m.id
            ORDER BY b.id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            boards = [Board.from_db(row) for row in rows]
            return render_template('board_list.html',boards=boards)
    finally:
        conn.close()

# 2. 게시글 자세히 보기
@app.route('/board/view/<int:board_id>') # http://localhost:5000/board/view/(게시물번호)
def board_view(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # JOIN을 통해 작성자 정보(name, uid)를 함께 조회
            sql = """
            SELECT b.*, m.name as writer_name, m.uid as writer_uid
            FROM boards b
            JOIN members m ON b.member_id = m.id
            WHERE b.id = %s
            """
            cursor.execute(sql, (board_id,))
            row = cursor.fetchone()
            print(row) # db에서 나온 dict타입 콘솔에 출력 테스트용
            if not row:
                return "<script>alert('존재하지 않는 게시글입니다.');history.back()</script>"
            # Boards 객체로 변환 (앞서 작성한 Boards.py의 from_db 활용)
            board = Board.from_db(row)

            return render_template('board_view.html',board=board)
    finally:
        conn.close()
@app.route('/board/edit/<int:board_id>',methods=['GET','POST'])
def board_edit(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 화면 보여주기 (기존 데이터 로드)
            if request.method == 'GET':
                sql = "SELECT * FROM boards WHERE id = %s"
                cursor.execute(sql,(board_id,))
                row = cursor.fetchone()

                if not row:
                    return "<script>alert('존재하지 않는 게시글입니다.');history.back()</script>"

                # 본인 확인 로직 (필요시 추가)
                if row['member_id'] != session.get('user_id'):
                    return "<script>alert('수정 권한이 없습니다.');history.back()</script>"
                print(row) # 콘솔에 출력 테스트용
                board = Board.from_db(row)
                return render_template('board_edit.html',board=board)

            # 2. 실제 DB 업데이트 처리
            elif request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')

                sql = "UPDATE boards SET title = %s, content = %s WHERE id = %s"
                cursor.execute(sql,(title,content,board_id))
                conn.commit()

                return redirect(url_for('board_view',board_id=board_id))
    finally:
        conn.close()

@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = 'DELETE FROM boards WHERE id = %s AND member_id = %s'
            cursor.execute(sql,(board_id,session['user_id']))
            conn.commit()

            if cursor.rowcount > 0:
                print(f"게시글 {board_id}번 삭제 성공")
                return redirect(url_for('board_list'))
            else:
                return "<script>alert('삭제할 수 없습니다.');history.back()</script>"
    except Exception as e:
        print(f"삭제 에러 : {e}")
        return "삭제 중 오류가 발생했습니다."
    finally:
        conn.close()


# 사용자가 선택한 위치 기준으로 주변 위험 사건을 조회하는 핵심 API
@app.route('/alerts')
def alert_page():
    search_lat = request.args.get('lat', type=float)
    search_lng = request.args.get('lng', type=float)
    search_address = request.args.get('address', '', type=str).strip()
    radius_m = request.args.get('radius_m', DEFAULT_RADIUS_M, type=int)

    search_city = request.args.get('city', '', type=str).strip()
    search_district = request.args.get('district', '', type=str).strip()

    user_role = session.get('user_role', 'user')
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    i.id,
                    i.member_id,
                    i.title,
                    i.location,
                    i.region_name,
                    i.latitude,
                    i.longitude,
                    i.image_path,
                    i.status,
                    i.risk_score,
                    i.first_created_at,
                    i.last_checked_at,

                    COUNT(r.id) + CASE WHEN i.member_id IS NOT NULL THEN 1 ELSE 0 END AS report_count,

                    (
                        SELECT COUNT(DISTINCT reporter_id)
                        FROM (
                            SELECT i2.member_id AS reporter_id
                            FROM incidents i2
                            WHERE i2.id = i.id

                            UNION

                            SELECT r2.member_id AS reporter_id
                            FROM incident_reports r2
                            WHERE r2.incident_id = i.id
                        ) AS all_reporters
                        WHERE reporter_id IS NOT NULL
                    ) AS reporter_count

                FROM incidents i
                LEFT JOIN incident_reports r
                    ON i.id = r.incident_id
                GROUP BY
                    i.id, i.member_id, i.title, i.location, i.region_name,
                    i.latitude, i.longitude, i.image_path, i.status,
                    i.risk_score, i.first_created_at, i.last_checked_at
                ORDER BY i.first_created_at DESC
            """
            cursor.execute(sql)
            incidents = cursor.fetchall()

        filtered_incidents = []

        for incident in incidents:
            incident_lat = incident.get('latitude')
            incident_lng = incident.get('longitude')
            incident_location = incident.get('location', '')

            # 관리자와 일반 사용자에게 표시되는 사건 기준을 분리하는 권한 기반 필터
            # 일반 사용자만 필터 적용
            if user_role not in ['admin', 'manager']:
                risk_score = float(incident.get('risk_score') or 0)
                reporter_count = int(incident.get('reporter_count') or 0)

                # 사용자 노출 기준
                visible_to_user = (
                        risk_score >= 80 or
                        (risk_score >= 50 and reporter_count >= 3)
                )

                if not visible_to_user:
                    continue

            if search_city:
                if search_district:
                    if search_city in incident_location and search_district in incident_location:
                        incident['distance_m'] = None
                        filtered_incidents.append(incident)
                else:
                    if search_city in incident_location:
                        incident['distance_m'] = None
                        filtered_incidents.append(incident)

            elif search_lat is not None and search_lng is not None:
                if incident_lat is None or incident_lng is None:
                    continue

                # 거리 계산 함수
                distance_m = haversine_m(search_lat, search_lng, incident_lat, incident_lng)

                if distance_m <= radius_m:
                    incident['distance_m'] = round(distance_m)
                    filtered_incidents.append(incident)

            else:
                incident['distance_m'] = None
                filtered_incidents.append(incident)

        if search_lat is not None and search_lng is not None:
            filtered_incidents.sort(key=lambda x: x['distance_m'])

        print("검색 주소:", search_address)
        print("필터 전 개수:", len(incidents))
        print("필터 후 개수:", len(filtered_incidents))

        display_address = search_address
        filter_type = 'all'

        if search_city:
            filter_type = 'region'
            if search_district:
                display_address = f"{search_city} {search_district}"
            else:
                display_address = f"{search_city} 전체"

        elif search_lat is not None and search_lng is not None:
            filter_type = 'radius'

        user_role = session.get('user_role', 'user')

        # 권한별 화면 분리
        template_name = 'alert.html'
        if user_role in ['admin', 'manager']:
            template_name = 'admin_alert.html'

        return render_template(
            template_name,
            incidents=filtered_incidents,
            selected_address=display_address,
            selected_lat=search_lat,
            selected_lng=search_lng,
            radius_m=radius_m,
            filter_type=filter_type,
            user_role=user_role
        )

    finally:
        conn.close()

####################################### 게시판 CRUD END ################################################################

@app.route('/')
def index():
    return render_template("main.html")

if __name__ == '__main__':
    app.run(host='172.30.1.22',port=5001,debug=True)