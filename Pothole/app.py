# ================================================================
# 📦 필요한 도구 (import)
# ================================================================

from flask import Flask, request, jsonify, send_from_directory, render_template
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import mysql.connector
from ultralytics import YOLO
from dotenv import load_dotenv
import cv2       # 프레임 추출용 (OpenCV)
import shutil    # 임시 프레임 폴더 정리
import threading # AI 백그라운드 분석용

# ================================================================
# ⚙️ 기본 설정
# ================================================================
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS       = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 영상 최대 100MB 제한

DB_CONFIG = {
    'host'    : os.getenv('DB_HOST'),
    'user'    : os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

model = YOLO('best_seg_pot_shink_100.pt')
load_dotenv()

# ================================================================
# ⚠️ 에러 핸들러 — 파일 크기 초과 (100MB)
# ================================================================
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "파일이 너무 커요! 영상은 100MB 이하만 가능해요."}), 413

# ================================================================
# 🔧 유틸 함수 0 — DB 연결
# ================================================================
def get_db():
    conn   = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    return conn, cursor

# ================================================================
# 🔧 유틸 함수 1 — 사진 파일 확장자 확인
# ================================================================
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================================================================
# 🔧 유틸 함수 1-2 — 영상 파일 확장자 확인
# ================================================================
def allowed_video_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

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
# 🤖 유틸 함수 3 — AI 이미지 분석 + 결과사진에 객체박스 그려주기
# ================================================================
def analyze_image(file_path):
    results = model(file_path)

    if len(results[0].boxes) == 0:
        return {
            "label"      : "unknown",
            "confidence" : 0.0,
            "result_path": None
        }

    confidence = float(results[0].boxes.conf[0])
    label      = results[0].names[int(results[0].boxes.cls[0])]

    # 바운딩박스 그린 이미지 저장
    result_filename = 'result_' + os.path.basename(file_path)
    result_path     = os.path.join(UPLOAD_FOLDER, result_filename)
    results[0].save(filename=result_path)

    return {
        "label"      : label,
        "confidence" : round(confidence, 2),
        "result_path": result_path
    }

# ================================================================
# 🎬 유틸 함수 4 — 영상에서 프레임 추출 (OpenCV)
# fps=1 → 1초당 1장만 추출해서 가볍게 처리
# ================================================================
def extract_frames(video_path, fps=1):
    base      = os.path.splitext(os.path.basename(video_path))[0]
    frame_dir = os.path.join(UPLOAD_FOLDER, f'frames_{base}')
    os.makedirs(frame_dir, exist_ok=True)

    cap       = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)   # 영상 원본 FPS
    interval  = int(video_fps / fps)         # 몇 프레임마다 1장 추출할지

    frames = []
    count  = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            frame_path = os.path.join(frame_dir, f'frame_{count:04d}.jpg')
            cv2.imwrite(frame_path, frame)
            frames.append(frame_path)
        count += 1

    cap.release()
    return sorted(frames), frame_dir

# ================================================================
# 🔁 유틸 함수 5 — 백그라운드 AI 분석 (접수 후 자동 실행)
# 제보자에게는 결과 노출 안 함 — DB에만 저장
# ================================================================
def run_ai_analysis(report_id, file_path, file_type):
    try:
        db, cursor = get_db()

        # ── 파일 타입별 분석 ──────────────────────────────
        if file_type == 'image':
            ai          = analyze_image(file_path)
            confidence  = ai['confidence']
            label       = ai['label']
            result_path = ai.get('result_path')

        else:  # video
            frames, frame_dir = extract_frames(file_path, fps=1)
            best_confidence  = 0.0
            best_result_path = None

            for frame_path in frames:
                ai = analyze_image(frame_path)
                if ai['confidence'] > best_confidence:
                    best_confidence  = ai['confidence']
                    best_result_path = ai.get('result_path')

            # 임시 프레임 폴더 정리
            shutil.rmtree(frame_dir, ignore_errors=True)

            confidence  = best_confidence
            label       = 'pothole'
            result_path = best_result_path

        # ── 상태 결정 ─────────────────────────────────────
        if confidence >= 0.8:
            status = 'auto_accepted'
        elif confidence >= 0.5:
            status = 'review_pending'
        else:
            status = 'ai_rejected'

        # ── DB 업데이트 ───────────────────────────────────
        cursor.execute("""
            UPDATE reports
            SET ai_label      = %s,
                ai_confidence = %s,
                result_path   = %s,
                status        = %s
            WHERE id = %s
        """, (label, round(confidence, 2), result_path, status, report_id))
        db.commit()

        # ── 상태 이력 기록 ────────────────────────────────
        cursor.execute("""
            INSERT INTO status_history
            (report_id, old_status, new_status, note)
            VALUES (%s, %s, %s, %s)
        """, (report_id, 'pending', status, 'AI 자동 분석'))
        db.commit()

        print(f'[AI 분석 완료] report_id={report_id} | {label} | {confidence} | {status}')

    except Exception as e:
        print(f'[AI 분석 오류] report_id={report_id} : {e}')

# ================================================================
# 🛣️ API 1 — 사진 제보 접수
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

    # ── 파일 크기 체크 (20MB) ──────────────────────────────
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 20 * 1024 * 1024:
        return jsonify({"error": "사진은 20MB 이하만 가능해요!"}), 400

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

    # ── STEP 5: DB 저장 (status=pending, AI는 백그라운드에서) ─
    cursor.execute("""
        INSERT INTO reports
        (user_id, file_path, file_type,
         latitude, longitude, address, region,
         status, parent_id, upload_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, file_path, 'image',
        latitude, longitude, address, region,
        'pending', parent_id,
        1 if parent_id is None else 0
    ))
    db.commit()
    report_id = cursor.lastrowid

    # ── STEP 6: 클러스터 처리 ──────────────────────────────
    if parent_id is None:
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
            cursor.execute("""
                UPDATE clusters SET report_count = report_count + 1 WHERE id = %s
            """, (cluster_id,))
        else:
            cursor.execute("""
                INSERT INTO clusters (center_lat, center_lon, region, report_count)
                VALUES (%s, %s, %s, 1)
            """, (latitude, longitude, region))
            cluster_id = cursor.lastrowid

        cursor.execute("""
            UPDATE reports SET cluster_id = %s WHERE id = %s
        """, (cluster_id, report_id))
        db.commit()

    # ── STEP 7: 백그라운드에서 AI 분석 시작 ────────────────
    thread = threading.Thread(
        target=run_ai_analysis,
        args=(report_id, file_path, 'image')
    )
    thread.daemon = True
    thread.start()

    # ── STEP 8: 제보자에게 접수 완료만 반환 ────────────────
    return jsonify({
        "message"  : "제보 접수 완료!",
        "report_id": report_id
    }), 200


# ================================================================
# 🛣️ API 2 — 영상 제보 접수
# POST /report/video
# ================================================================
@app.route('/report/video', methods=['POST'])
def upload_video():
    db, cursor = get_db()

    # ── STEP 1: 파일 확인 ──────────────────────────────────
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없어요!"}), 400

    file = request.files['file']
    if not allowed_video_file(file.filename):
        return jsonify({"error": "mp4, avi, mov 파일만 가능해요!"}), 400

    # ── 파일 크기 체크 (100MB) ─────────────────────────────
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 100 * 1024 * 1024:
        return jsonify({"error": "영상은 100MB 이하만 가능해요!"}), 400

    # ── STEP 2: 파일 저장 ──────────────────────────────────
    filename  = secure_filename(file.filename)
    filename  = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # ── STEP 3: 위치 확인 (영상은 지도에서 직접 선택) ──────
    latitude  = request.form.get('latitude')
    longitude = request.form.get('longitude')

    if not latitude or not longitude:
        return jsonify({
            "error"         : "위치 정보가 없어요!",
            "needs_location": True
        }), 400

    latitude  = float(latitude)
    longitude = float(longitude)

    address = request.form.get('address', None)
    region  = request.form.get('region',  None)
    user_id = request.form.get('user_id', None)  # 임시! 팀원 로그인 완성 후 session으로 교체

    # ── STEP 4: DB 저장 (status=pending, AI는 백그라운드에서) ─
    cursor.execute("""
        INSERT INTO reports
        (user_id, file_path, file_type,
         latitude, longitude, address, region,
         status, upload_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, file_path, 'video',
        latitude, longitude, address, region,
        'pending', 1
    ))
    db.commit()
    report_id = cursor.lastrowid

    # ── STEP 5: 백그라운드에서 AI 분석 시작 ────────────────
    thread = threading.Thread(
        target=run_ai_analysis,
        args=(report_id, file_path, 'video')
    )
    thread.daemon = True
    thread.start()

    # ── STEP 6: 제보자에게 접수 완료만 반환 ────────────────
    return jsonify({
        "message"  : "제보 접수 완료!",
        "report_id": report_id
    }), 200


# ================================================================
# 📋 API 3 — 민원 진행 상황 확인
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


if __name__ == '__main__':
    app.run(debug=True, port=5678)