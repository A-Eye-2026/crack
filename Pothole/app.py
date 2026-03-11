# ================================================================
# 📦 필요한 도구 (import)
# ================================================================

from flask import Flask, request, jsonify ,send_from_directory, render_template
# Flask       → 웹 서버 만드는 도구, pip install flask pillow mysql-connector-python werkzeug 플라스크 설치
# request     → 사용자가 보낸 데이터(파일, 텍스트 등) 꺼내는 도구
# jsonify     → 파이썬 딕셔너리를 JSON 형식으로 바꿔주는 도구
#               (API 응답할 때 항상 JSON으로 보내야 해서 필요함)

from PIL import Image
from PIL.ExifTags import TAGS,GPSTAGS
# PIL(Pillow)  → 이미지 파일 열고 분석하는 도구
# TAGS        → EXIF 숫자코드 → 이름으로 변환 (예: 34853 → 'GPSInfo')
# GPSTAGS     → GPS 숫자코드 → 이름으로 변환 (예: 2 → 'GPSLatitude')

from datetime import datetime
# datetime    → 현재 날짜/시간 가져오는 도구
#               파일 이름에 시간 붙일 때 사용

from werkzeug.utils import secure_filename
# secure_filename → 파일 이름에서 위험한 문자 제거해주는 도구
#                   예: "../../../etc/passwd.jpg" → "passwd.jpg" 로 안전하게 변환

import os
# os     -> 폴더 만들기 , 파일경로 합치기 등 운영체제 관련

import mysql.connector #pip install mysql-connector-python

# ================================================================
# ⚙️ 기본 설정
# ================================================================
app = Flask(__name__)
# Flask 앱생성 -> 웹 서버 본체
# __name__ "현재 이 파일을 실행해"

UPLOAD_FOLDER = 'uploads'
# 업로드된 사진을 저장할 폴더 이름
# 실제 경로 : C:\004.miniproject\Pothole\uploads

ALLOWED_EXTENSIONS = (['png', 'jpg', 'jpeg'])

# 허용할 파일 확장자 목록

os.makedirs(UPLOAD_FOLDER,exist_ok=True)
# 업로드 폴더 없으면 자동 생성
# exist_ok=True -> 이미있어도 오류 안냄

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# flask 앱에 업로드폴더 어딘지 알려주는 설정

DB_CONFIG = {
    'host'    : 'localhost',
    'user'    : 'road',        # ← MySQL 아이디
    'password': '1234',        # ← MySQL 비밀번호
    'database': 'road'   # ← 만든 DB
}

# ================================================================
# 🔧 유틸 함수 0 — DB연결 확인
# ================================================================
def get_db():
    """DB 연결 반환"""
    conn   = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    # dictionary=True → 결과를 딕셔너리로 반환
    # 예: (1, 'pothole') 대신 {'id': 1, 'label': 'pothole'}
    return conn, cursor

# ================================================================
# 🔧 유틸 함수 1 — 파일 확장자 확인
# ================================================================
def allowed_file(filename):

    return'.'in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
        # '.' in filename
        #   → 파일 이름에 점(.)이 있는지 확인 (확장자가 있는지)
        #   → "사진jpg" 같은 이상한 이름 걸러냄

        # filename.rsplit('.', 1)[1]
        #   → 점(.)을 기준으로 뒤쪽만 가져옴
        #   → "사진.jpg" → ["사진", "jpg"] → [1] → "jpg"

        # .lower()
        #   → 대문자를 소문자로 변환
        #   → "JPG", "Jpg" 도 통과되게

        # in ALLOWED_EXTENSIONS
        #   → {'jpg', 'jpeg', 'png'} 안에 있으면 True 반환

# ================================================================
# 🔧 유틸 함수 2 — 사진에서 GPS 좌표 추출
# ================================================================

def get_gps_from_exif(image_path):
    # image_path: 저장된 사진 파일 경로
    # 반환값: (위도, 경도) 또는 GPS 없으면 (None, None)
    try:
        image = Image.open(image_path)
        # 사진파일 열기
        exif_data = image._getexif()
        # 사진안에 숨겨진 EXIF 정보 꺼내기
        # 결과 :  {271: 'Samsung', 34853: {1: 'N', 2: (37, 33, 59), ...}, ...}
        # 숫자들이 태그 코드
        if not exif_data :
            return None, None
            # EXIF 자체 없는 사진
        labeled = {TAGS.get(k,k): v for k, v in exif_data.items()}
        # 숫자코드 -> 이름으로 변환
        # {271: 'Samsung'} → {'Make': 'Samsung'}
        # {34853: {...}}   → {'GPSInfo': {...}}
        # 사람이 읽기 쉽게

        gps_info = labeled.get('GPSInfo')
        # GPS 정보만 꺼내기
        # 결과: {1: 'N', 2: (37, 33, 59), 3: 'E', 4: (126, 58, 41), ...}

        if not gps_info:
            return None, None
            # GPS 정보가 없는 사진

        gps = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}

        # GPS 숫자 코드도 이름으로 변환
        # {1: 'N', 2: (37,33,59)} → {'GPSLatitudeRef': 'N', 'GPSLatitude': (37,33,59)}

        def dms_to_decimal(dms,ref):
        # GPS 좌표는 도/분/초(DMS) 형식으로 저장돼 있어요
        # 예: 37도 33분 59초 N
        # 이걸 우리가 쓰는 십진수(37.5664)로 변환하는 함수

            d = float(dms[0])  # 도 (degrees)   예: 37
            m = float(dms[1])  # 분 (minutes)   예: 33
            s = float(dms[2])  # 초 (seconds)   예: 59
            result = d + m / 60 + s / 3600
            return -result if ref in ['S', 'W'] else round(result, 6)
            # 남위(S)나 서경(W)이면 음수로 변환
            # 예: 남위 37도 → -37.5664
            # 소수점 6자리까지 반올림

        lat = dms_to_decimal(gps['GPSLatitude'],  gps['GPSLatitudeRef'])
        # 위도 계산 예: 37.566418

        lon = dms_to_decimal(gps['GPSLongitude'], gps['GPSLongitudeRef'])
        # 경도 계산 예: 126.977943

        return lat, lon
        # 최종 반환: (37.566418, 126.977943)
    except:
        return None, None
        # 뭔가 잘못돼도 None 반환 (에러로 서버 죽는 거 방지)

# ================================================================
# 🤖 유틸 함수 3 — AI 이미지 분석 (임시 가짜 함수)
# ================================================================

def analyze_image(file_path):
    # ⚠️ 지금은 테스트용 가짜 결과를 반환해요
    # 나중에 팀원이 만든 YOLO 코드로 이 함수만 교체하면 됨!
    # 함수 이름이랑 반환 형식만 유지하면 돼요

    return {
        "label": "pothole",    # 탐지된 객체 종류
        "confidence": 0.92     # AI 신뢰도 (0~1 사이, 1에 가까울수록 확실)
    }


# ================================================================
# 🛣️ API 1 — 이미지 신고 업로드
# POST /report/image
# ================================================================
@app.route('/report/image', methods=['POST'])
# @app.route → 이 함수를 특정 URL에 연결해주는 데코레이터
# '/report/image' → 사용자가 이 주소로 요청하면 아래 함수 실행
# methods=['POST'] → POST 방식만 허용 (파일 전송할 때 POST 사용)

def upload_image():
    db, cursor = get_db()

    # ── STEP 1: 파일 있는지 확인 ──────────────────────────
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없어요!"}), 400
        # request.files → 사용자가 보낸 파일들의 목록
        # 'file' 키가 없으면 → 에러 반환
        # 400 → "잘못된 요청" 상태 코드

    file = request.files['file']
    # 사용자가 보낸 파일 꺼내기

    if not allowed_file(file.filename):
        return jsonify({"error": "jpg, png 파일만 가능해요!"}), 400
        # 위에서 만든 확장자 확인 함수로 걸러냄

    # ── STEP 2: 파일 저장 ──────────────────────────────────
    filename = secure_filename(file.filename)
    # 파일 이름에서 위험한 문자 제거
    # 예: "../hack.jpg" → "hack.jpg"

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    # 파일 이름 앞에 현재 시간 붙이기
    # 예: "20240309_143022_도로사진.jpg"
    # 같은 이름 파일이 와도 덮어쓰기 안 됨!

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    # 저장 경로 만들기
    # 예: "uploads/20240309_143022_도로사진.jpg"

    file.save(file_path)
    # 실제로 파일 저장!

    # ── STEP 3: GPS 추출 ───────────────────────────────────
    lat, lon = get_gps_from_exif(file_path)
    # 위에서 만든 함수로 GPS 꺼내기
    # GPS 있으면: lat=37.566418, lon=126.977943
    # GPS 없으면: lat=None,      lon=None

    if lat is None:
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        # GPS가 없으면 → 프론트에서 지도 클릭한 좌표 받기
        # request.form → 사용자가 폼으로 보낸 텍스트 데이터

    if not lat or not lon:
        return jsonify({
            "error": "위치 정보가 없어요!",
            "needs_location": True
            # 프론트엔드에서 이 값을 보고 지도를 띄워줌
        }), 400
    # 변수명 통일 (lat/lon → latitude/longitude)
    latitude  = float(lat)
    longitude = float(lon)

    # form에서 추가 데이터 받기
    address = request.form.get('address', None)
    region  = request.form.get('region',  None)

    # 임시 user_id (팀원 로그인 기능 완성되면 교체!)
    user_id = request.form.get('user_id', None)

    # ── STEP 4: 동일 유저, 동일 제보 중복 체크  ───────────────────────────────────
    # 같은 유저가 최근 24시간 내에
    # 비슷한 위치(반경 50m)에 올린 신고가 있으면 막기
    cursor.execute("""
        SELECT id FROM reports
        WHERE user_id = %s
          AND status = 'ai_rejected'
          AND created_at > NOW() - INTERVAL 24 HOUR
          AND ST_Distance_Sphere(
              POINT(longitude, latitude),
              POINT(%s, %s)
          ) < 50
        LIMIT 1
    """, (user_id, longitude, latitude))

    existing = cursor.fetchone()
    parent_id = existing['id'] if existing else None

    # ── STEP 5: AI 분석 ────────────────────────────────────
    ai = analyze_image(file_path)
    confidence = ai['confidence']

    # 기본 status 결정
    if confidence >= 0.8:
        status = 'auto_accepted'
    else:
        status = 'ai_rejected'

    # ── STEP 6: DB 저장 (다음 단계에서 추가) ──────────────
    cluster_id = None  # ← 먼저 None 으로 초기화!

    cursor.execute("""
           INSERT INTO reports
           (user_id, file_path, file_type,
            latitude, longitude, address, region,
            ai_label, ai_confidence,
            status, parent_id, upload_count)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
       """, (
        user_id, file_path, 'image',
        lat, lon, address, region,
        ai['label'], confidence,
        status, parent_id,
        1 if parent_id is None else 0  # 재업로드면 카운트 0
    ))
    db.commit()
    report_id = cursor.lastrowid

    # ── STEP 7: 클러스터 카운트 ──────────────────
    @app.route('/report/image', methods=['POST'])
    def upload_image():

        # ── STEP 1: 파일 확인 ──────────────────────────────────
        if 'file' not in request.files:
            return jsonify({"error": "파일이 없어요!"}), 400

        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({"error": "jpg, png 파일만 가능해요!"}), 400

        # ── STEP 2: 파일 저장 ──────────────────────────────────
        filename = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # ── STEP 3: GPS + 주소 추출 ────────────────────────────
        lat, lon = get_gps_from_exif(file_path)

        if lat is None:
            lat = request.form.get('latitude')
            lon = request.form.get('longitude')

        if not lat or not lon:
            return jsonify({
                "error": "위치 정보가 없어요!",
                "needs_location": True
            }), 400

        address = request.form.get('address', None)  # ← 추가!
        region = request.form.get('region', None)  # ← 추가!

        # ── STEP 4: 중복 체크 ──────────────────────────────────
        cursor.execute("""
            SELECT id FROM reports
            WHERE user_id = %s
              AND status = 'ai_rejected'
              AND created_at > NOW() - INTERVAL 24 HOUR
              AND ST_Distance_Sphere(
                  POINT(longitude, latitude),
                  POINT(%s, %s)
              ) < 50
            LIMIT 1
        """, (user_id, lon, lat))

        existing = cursor.fetchone()
        parent_id = existing['id'] if existing else None

        # ── STEP 5: AI 분석 ────────────────────────────────────
        ai = analyze_image(file_path)
        confidence = ai['confidence']

        if confidence >= 0.8:
            status = 'auto_accepted'
        else:
            status = 'ai_rejected'

        # ── STEP 6: DB 저장 ────────────────────────────────────
        cluster_id = None

        cursor.execute("""
            INSERT INTO reports
            (user_id, file_path, file_type,
             latitude, longitude, address, region,
             ai_label, ai_confidence,
             status, parent_id, upload_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, file_path, 'image',
            lat, lon, address, region,
            ai['label'], confidence,
            status, parent_id,
            1 if parent_id is None else 0
        ))
        db.commit()
        report_id = cursor.lastrowid

        # ── STEP 7: 클러스터 카운트 ────────────────────────────
        if parent_id is None:  # ← 최초 신고일 때만! ✅
            cursor.execute("""
                SELECT id, report_count FROM clusters
                WHERE ST_Distance_Sphere(
                    POINT(center_lon, center_lat),
                    POINT(%s, %s)
                ) < 100
                LIMIT 1
            """, (lon, lat))

            existing_cluster = cursor.fetchone()

            if existing_cluster:
                cluster_id = existing_cluster['id']
                new_count = existing_cluster['report_count'] + 1

                cursor.execute("""
                    UPDATE clusters
                    SET report_count = %s WHERE id = %s
                """, (new_count, cluster_id))

                if new_count >= 3 and status == 'ai_rejected':
                    status = 'review_pending'
                    cursor.execute("""
                        UPDATE reports SET status = 'review_pending'
                        WHERE id = %s
                    """, (report_id,))
            else:
                cursor.execute("""
                    INSERT INTO clusters
                    (center_lat, center_lon, region, report_count)
                    VALUES (%s, %s, %s, 1)
                """, (lat, lon, region))
                cluster_id = cursor.lastrowid

            cursor.execute("""
                UPDATE reports SET cluster_id = %s WHERE id = %s
            """, (cluster_id, report_id))
            db.commit()
        # else: 재업로드면 아무것도 안 함 ✅

        # ── STEP 8: 상태 변경 이력 기록 ────────────────────────
        cursor.execute("""
            INSERT INTO status_history
            (report_id, old_status, new_status, note)
            VALUES (%s, %s, %s, %s)
        """, (report_id, 'update', status, 'AI 자동 분석'))
        db.commit()

        # ── STEP 9: 결과 반환 ──────────────────────────────────
        return jsonify({
            "message": "포트홀 제보 접수 완료!",
            "report_id": report_id,  # ← 추가!
            "file_path": file_path,
            "location": {"latitude": lat, "longitude": lon},
            "ai_result": {**ai, "status": status}
        }), 200


# ================================================================
# 📋 API 2 — 민원 진행 상황 확인
# GET /report/status/1  (1번 신고 조회)
# GET /report/status/5  (5번 신고 조회)
# ================================================================

@app.route('/report/status/<int:report_id>', methods=['GET'])
# <int:report_id> → URL에서 숫자를 변수로 받음
# /report/status/1 → report_id = 1
# /report/status/5 → report_id = 5

def get_status(report_id):
    # TODO: 지금은 가짜 데이터, 나중에 DB에서 실제 데이터 가져올 거예요

    return jsonify({
        "report_id": report_id,
        "status": "처리중",
        "created_at": "2024-03-09"
    }), 200







@app.route('/report_pothole')
def report_page():
    return render_template('report_pothole.html')

@app.route('/report/video', methods=['POST'])
def upload_video():
    # 나중에 구현 (지금은 이미지랑 거의 동일)
    pass

@app.route('/dashboard_admin')
def dashboard_admin():
    return render_template('dashboard_admin.html')

if __name__ == '__main__':
    app.run(debug=True, port=5678)


