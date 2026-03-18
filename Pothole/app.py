# ================================================================
# 📦 필요한 도구 (import)
# ================================================================

from flask import Flask, request, jsonify ,send_from_directory, render_template
from PIL import Image
from PIL.ExifTags import TAGS,GPSTAGS
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import mysql.connector
from ultralytics import YOLO

# ================================================================
# ⚙️ 기본 설정
# ================================================================
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = (['png', 'jpg', 'jpeg'])

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_CONFIG = {
    'host'    : 'localhost',
    'user'    : 'road',
    'password': '1234',
    'database': 'road'
}

model = YOLO('best.pt')
# ================================================================
# 🔧 유틸 함수 0 — DB 연결
# ================================================================
def get_db():
    conn   = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    return conn, cursor

# ================================================================
# 🔧 유틸 함수 1 — 파일 확장자 확인
# ================================================================
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================================================================
# 🔧 유틸 함수 2 — 사진에서 GPS 좌표 추출
# ================================================================
def get_gps_from_exif(image_path):
    try:
        image     = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None, None

        labeled  = {TAGS.get(k, k): v for k, v in exif_data.items()}
        gps_info = labeled.get('GPSInfo')
        if not gps_info:
            return None, None

        gps = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}

        def dms_to_decimal(dms, ref):
            d      = float(dms[0])
            m      = float(dms[1])
            s      = float(dms[2])
            result = d + m / 60 + s / 3600
            return -result if ref in ['S', 'W'] else round(result, 6)

        lat = dms_to_decimal(gps['GPSLatitude'],  gps['GPSLatitudeRef'])
        lon = dms_to_decimal(gps['GPSLongitude'], gps['GPSLongitudeRef'])
        return lat, lon
    except:
        return None, None

# ================================================================
# 🤖 유틸 함수 3 — AI 이미지 분석 (임시 가짜 함수) + 결과사진에 객체박스그려주기
# ================================================================
def analyze_image(file_path):
    results = model(file_path)

    if len(results[0].boxes) == 0:
        return {
            "label": "unknown",
            "confidence": 0.0,
            "result_path": None
        }

    confidence = float(results[0].boxes.conf[0])
    label = results[0].names[int(results[0].boxes.cls[0])]

    # 바운딩박스 그린 이미지 저장
    result_path = file_path.replace('uploads/', 'uploads/result_')
    results[0].save(filename=result_path)

    return {
        "label": label,
        "confidence": round(confidence, 2),
        "result_path": result_path
    }

# ================================================================
# 🛣️ API 1 — 이미지 신고 업로드
# POST /report/image
# ================================================================
@app.route('/report/image', methods=['POST'])
def upload_image():
    db, cursor = get_db()

    # ── STEP 1: 파일 확인 ──────────────────────────────────
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없어요!"}), 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({"error": "jpg, png 파일만 가능해요!"}), 400

    # ── STEP 2: 파일 저장 ──────────────────────────────────
    filename  = secure_filename(file.filename)
    filename  = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # ── STEP 3: GPS + 주소 추출 ────────────────────────────
    lat, lon = get_gps_from_exif(file_path)

    if lat is None:
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')

    if not lat or not lon:
        return jsonify({
            "error"         : "위치 정보가 없어요!",
            "needs_location": True
        }), 400

    latitude  = float(lat)
    longitude = float(lon)

    address = request.form.get('address', None)
    region  = request.form.get('region',  None)
    user_id = request.form.get('user_id', None)  # 임시! 팀원 로그인 완성 후 session으로 교체

    # ── STEP 4: 동일 유저 중복 체크 (24시간, 반경 50m) ─────
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

    existing  = cursor.fetchone()
    parent_id = existing['id'] if existing else None

    # ── STEP 5: AI 분석 ────────────────────────────────────
    ai         = analyze_image(file_path)
    confidence = ai['confidence']

    if confidence >= 0.8:
        status = 'auto_accepted'
    elif confidence >= 0.5:
        status = 'review_pending'
    else:
        status = 'ai_rejected'

    # ── STEP 6: DB 저장 ────────────────────────────────────
    cluster_id = None

    cursor.execute("""
        INSERT INTO reports
        (user_id, file_path, file_type, result_path,
         latitude, longitude, address, region,
         ai_label, ai_confidence,
         status, parent_id, upload_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, file_path, 'image', ai.get('result_path'),
        latitude, longitude, address, region,
        ai['label'], confidence,
        status, parent_id,
        1 if parent_id is None else 0
    ))
    db.commit()
    report_id = cursor.lastrowid

    # ── STEP 7: 클러스터 카운트 + review_pending 판단 ──────
    # 조건 ①: 신뢰도 0.5 이상 0.8 미만 (애매한 신고)
    # 조건 ②: 반경 100m 내에 다른 아이디 신고가 존재할 때
    # → 두 조건 모두 충족하면 관리자에게 review_pending 알림

    if parent_id is None:  # 최초 신고일 때만!

        # 반경 100m 내 기존 클러스터 찾기
        cursor.execute("""
            SELECT id, report_count FROM clusters
            WHERE ST_Distance_Sphere(
                POINT(center_lon, center_lat),
                POINT(%s, %s)
            ) < 100
            LIMIT 1
        """, (longitude, latitude))

        existing_cluster = cursor.fetchone()

        if existing_cluster:
            cluster_id = existing_cluster['id']
            new_count  = existing_cluster['report_count'] + 1

            # 클러스터 카운트 업데이트
            cursor.execute("""
                UPDATE clusters SET report_count = %s WHERE id = %s
            """, (new_count, cluster_id))

            # ── review_pending 판단 ─────────────────────────
            # 조건 ①: 신뢰도 0.5 이상 0.8 미만
            if 0.5 <= confidence < 0.8:

                # 조건 ②: 같은 클러스터에 다른 아이디 신고 있는지 확인
                cursor.execute("""
                    SELECT id FROM reports
                    WHERE cluster_id = %s
                      AND user_id != %s
                      AND ST_Distance_Sphere(
                          POINT(longitude, latitude),
                          POINT(%s, %s)
                      ) < 100
                    LIMIT 1
                """, (cluster_id, user_id, longitude, latitude))

                other_user_report = cursor.fetchone()

                if other_user_report:
                    # 두 조건 모두 충족 → 관리자 검토 요청!
                    status = 'review_pending'
                    cursor.execute("""
                        UPDATE reports SET status = 'review_pending'
                        WHERE id = %s
                    """, (report_id,))

        else:
            # 클러스터 없으면 새로 생성
            cursor.execute("""
                INSERT INTO clusters
                (center_lat, center_lon, region, report_count)
                VALUES (%s, %s, %s, 1)
            """, (latitude, longitude, region))
            cluster_id = cursor.lastrowid

        # 신고에 cluster_id 연결
        cursor.execute("""
            UPDATE reports SET cluster_id = %s WHERE id = %s
        """, (cluster_id, report_id))
        db.commit()

    # ── STEP 8: 상태 변경 이력 기록 ────────────────────────
    cursor.execute("""
        INSERT INTO status_history
        (report_id, old_status, new_status, note)
        VALUES (%s, %s, %s, %s)
    """, (report_id, 'update', status, 'AI 자동 분석'))
    db.commit()

    # ── STEP 9: 결과 반환 ──────────────────────────────────
    return jsonify({
        "message"   : "포트홀 제보 접수 완료!",
        "report_id" : report_id,
        "file_path" : file_path,
        "location"  : {"latitude": latitude, "longitude": longitude},
        "ai_result" : {**ai, "status": status}
    }), 200


# ================================================================
# 📋 API 2 — 민원 진행 상황 확인
# GET /report/status/<id>
# ================================================================
@app.route('/report/status/<int:report_id>', methods=['GET'])
def get_status(report_id):
    # TODO: DB에서 실제 데이터 가져오기
    return jsonify({
        "report_id" : report_id,
        "status"    : "처리중",
        "created_at": "2024-03-09"
    }), 200


# ================================================================
# 🖥️ 페이지 라우트
# ================================================================
@app.route('/report_pothole')
def report_page():
    return render_template('report_pothole.html')

@app.route('/dashboard_admin')
def dashboard_admin():
    return render_template('dashboard_admin.html')

@app.route('/report/video', methods=['POST'])
def upload_video():
    pass  # 나중에 구현

if __name__ == '__main__':
    app.run(debug=True, port=5678)