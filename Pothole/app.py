import os
import sys
import uuid
import socket
import json
import time
import pymysql
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from dotenv import load_dotenv

# 로컬 실행을 위한 경로 설정
load_dotenv(os.path.join(os.path.dirname(__file__), 'secrets', '.env'))

# 리팩토링된 서비스들 임포트
from MachineLearning.routes import ml_bp
from game.routes import game_bp
from service.MemberService import MemberService
from service.BoardService import BoardService
from service.ScoreService import ScoreService
from service.PostService import PostService
from service.ProductService import ProductService
from service.OrderService import OrderService
from service.LikeService import LikeService
from service.AiDetectService import AiDetectService
from service.AiVideoService import AiVideoService
from common.session import Session
from common.ViewTracker import ViewTracker

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'aeye_secret_key_2026')

# ── 업로드 폴더 설정 ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# 업로드 폴더 자동 생성
os.makedirs(os.path.join(UPLOAD_FOLDER, 'ai_detect'), exist_ok=True)

# 블루프린트 등록 (ML, Game)
app.register_blueprint(ml_bp)
app.register_blueprint(game_bp)

# WASM MIME 타입 등록 (Stockfish.js 엔진용)
import mimetypes
mimetypes.add_type('application/wasm', '.wasm')

# YOLO 모델 로드
from ultralytics import YOLO
model = YOLO('yolov8n.pt')

# OpenCV 임포트
import cv2
import numpy as np

# jinja2 필터: JSON 문자열 → 객체
@app.template_filter('from_json')
def from_json_filter(value):
    return json.loads(value) if value else []

# ---------------------------------------------------------
# 공통 기능 (방문자 추적, 통계 주입)
# ---------------------------------------------------------

@app.before_request
def track_visitor():
    exclude_paths = ['/static', '/favicon.ico']
    if any(request.path.startswith(p) for p in exclude_paths):
        return
    if not request.cookies.get('visited_today'):
        if ViewTracker.check_and_track_view('visitor'):
            conn = Session.get_connection()
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql = """
                        UPDATE site_stats 
                        SET 
                            total_visits = total_visits + 1,
                            today_visits = CASE WHEN last_date < CURDATE() THEN 1 ELSE today_visits + 1 END,
                            last_date = CURDATE()
                        WHERE id = 1
                    """
                    cursor.execute(sql)
                    conn.commit()
            except Exception as e:
                print(f"Visitor Tracking Error: {e}")
            finally:
                conn.close()

@app.context_processor
def inject_site_stats():
    conn = Session.get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT total_visits, today_visits FROM site_stats WHERE id = 1")
            stats = cursor.fetchone()
            return dict(site_stats=stats)
    except:
        return dict(site_stats={'total_visits': 0, 'today_visits': 0})
    finally:
        conn.close()

# ---------------------------------------------------------
# 핵심 라우트 (Index, Auth)
# ---------------------------------------------------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('layout.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    uid = request.form.get('uid')
    upw = request.form.get('upw')
    user = MemberService.login(uid, upw)
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_uid'] = user['uid']
        session['user_role'] = user['role']
        return redirect(url_for('index'))
    return "<script>alert('로그인 실패'); history.back();</script>"

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
    name = request.form.get('name')
    success, msg = MemberService.signup(uid, password, name)
    if success:
        return "<script>alert('회원가입 완료! 로그인해주세요.'); location.href='/login';</script>"
    return f"<script>alert('{msg}'); history.back();</script>"

@app.route('/login/google', methods=['POST'])
def login_google():
    """Firebase ID Token 검증 후 세션 저장"""
    try:
        import firebase_admin
        from firebase_admin import auth as fb_auth, credentials as fb_cred
        # Firebase Admin 초기화 (중복 방지)
        if not firebase_admin._apps:
            cred_path = os.path.join(BASE_DIR, 'secrets', 'firebase-key.json')
            cred = fb_cred.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        data = request.json
        id_token = data.get('idToken')
        decoded = fb_auth.verify_id_token(id_token)
        uid = decoded.get('uid')
        email = decoded.get('email', '')
        name = decoded.get('name', email.split('@')[0] if email else '구글유저')
        photo = decoded.get('picture', None)

        user = MemberService.google_login_or_signup(uid, email, name, photo)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_uid'] = user['uid']
            session['user_role'] = user.get('role', 'user')
            return jsonify({'success': True, 'redirect': '/'})
        return jsonify({'success': False, 'message': '로그인 처리 실패'})
    except Exception as e:
        print(f"Google Login Error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/login/kakao/callback')
def kakao_callback():
    """카카오 인가 코드로 토큰 교환 후 로그인"""
    code = request.args.get('code')
    if not code:
        return redirect(url_for('login'))
    try:
        rest_key = os.environ.get('KAKAO_REST_API_KEY', '')
        client_secret = os.environ.get('KAKAO_CLIENT_SECRET', '')
        redirect_uri = request.host_url.rstrip('/') + '/login/kakao/callback'

        # 토큰 교환
        token_res = requests.post('https://kauth.kakao.com/oauth/token', data={
            'grant_type': 'authorization_code',
            'client_id': rest_key,
            'redirect_uri': redirect_uri,
            'code': code,
            'client_secret': client_secret
        })
        access_token = token_res.json().get('access_token')

        # 사용자 정보 요청
        user_res = requests.get('https://kapi.kakao.com/v2/user/me',
                                headers={'Authorization': f'Bearer {access_token}'})
        kakao_data = user_res.json()
        kakao_id = kakao_data.get('id')
        kakao_account = kakao_data.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        nickname = profile.get('nickname', f'카카오{kakao_id}')
        photo = profile.get('profile_image_url', None)
        email = kakao_account.get('email', None)

        user = MemberService.kakao_login_or_signup(kakao_id, nickname, photo, email)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_uid'] = user['uid']
            session['user_role'] = user.get('role', 'user')
            return redirect(url_for('index'))
        return "<script>alert('카카오 로그인 실패'); location.href='/login';</script>"
    except Exception as e:
        print(f"Kakao Callback Error: {e}")
        return "<script>alert('카카오 로그인 오류'); location.href='/login';</script>"

# ---------------------------------------------------------
# LMS 메뉴 (게시판, 성적)
# ---------------------------------------------------------

@app.route('/board')
def board_list():
    boards = BoardService.get_list(member_id=session.get('user_id'))
    return render_template('board_list.html', boards=boards)

@app.route('/board/view/<int:board_id>')
def board_view(board_id):
    board = BoardService.get_view(board_id)
    return render_template('board_view.html', board=board)

@app.route('/score/my')
def score_my():
    if 'user_id' not in session: return redirect(url_for('login'))
    score = ScoreService.get_my_score(session['user_id'])
    return render_template('score_my.html', score=score)

# ---------------------------------------------------------
# AI 이미지 객체 탐지 (YOLO)
# ---------------------------------------------------------

@app.route('/ai-detect', methods=['GET'])
def ai_detect_board():
    posts = AiDetectService.get_all_posts()
    return render_template('ai_detect/list.html', posts=posts)


@app.route('/ai-detect/write', methods=['GET', 'POST'])
def write_ai_detect():
    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename:
            # 파일명 생성 (UUID)
            ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{ext}"

            # 원본 저장 경로
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ai_detect', filename)
            file.save(save_path)

            # YOLO 예측 및 박싱 처리
            results = model.predict(save_path)

            # 박스가 그려진 이미지 생성 및 저장
            res_plotted = results[0].plot()
            annotated_filename = f"box_{filename}"
            annotated_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ai_detect', annotated_filename)
            cv2.imwrite(annotated_path, res_plotted)

            # 상세 탐지 결과 추출
            detailed_results = []
            for box in results[0].boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                name = model.names[cls]
                coords = box.xyxy[0].tolist()
                detailed_results.append({
                    'name': name,
                    'conf': round(conf * 100, 2),
                    'bbox': [round(x, 1) for x in coords]
                })

            # DB 저장
            AiDetectService.save_detect_post(
                session.get('user_id'),
                request.form.get('title', '제목없음'),
                request.form.get('content', ''),
                f"uploads/ai_detect/{filename}",
                json.dumps(detailed_results)
            )

            return render_template('ai_detect/result.html',
                                   img_url=f"uploads/ai_detect/{annotated_filename}",
                                   results=detailed_results)

    return render_template('ai_detect/write.html')


@app.route('/ai-detect/view/<int:post_id>')
def ai_detect_view(post_id):
    conn = Session.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_detect_posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    cursor.close()
    conn.close()

    if not post:
        return "<script>alert('해당 기록을 찾을 수 없습니다.'); history.back();</script>"

    saved_results = json.loads(post['detect_result']) if post['detect_result'] else []
    path_parts = post['image_path'].split('/')
    # image_path: uploads/ai_detect/filename.jpg → box_ prefix 삽입
    annotated_url = f"{path_parts[0]}/{path_parts[1]}/box_{path_parts[2]}" if len(path_parts) == 3 else post['image_path']

    return render_template('ai_detect/result.html',
                           img_url=annotated_url,
                           results=saved_results,
                           post=post)
                           
@app.route('/ai-detect/delete/<int:post_id>', methods=['POST'])
def ai_detect_delete(post_id):
    if session.get('user_role') != 'manager':
        return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"
    
    if AiDetectService.delete_post(post_id):
        return "<script>alert('삭제되었습니다.'); location.href='/ai-detect';</script>"
    return "<script>alert('삭제 실패'); history.back();</script>"

# ---------------------------------------------------------
# AI 영상 객체 탐지 (YOLO)
# ---------------------------------------------------------

@app.route('/ai-detect/video')
def video_list():
    conn = Session.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_video_posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('ai_detect/video_list.html', posts=posts)


@app.route('/ai-detect/video/write')
def write_video_form():
    return render_template('ai_detect/video_write.html')


def process_video_ai(video_post_id, origin_path, filename):
    cap = cv2.VideoCapture(origin_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_filename = f"{filename.split('.')[0]}.mp4" if filename.startswith('res_') else f"res_{filename.split('.')[0]}.mp4"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ai_detect', output_filename)

    # 브라우저 호환성을 위해 avc1 (H.264) 사용 시도
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, verbose=False)

        detected_objects = []
        for box in results[0].boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = model.names[cls]
            coords = box.xyxy[0].tolist()
            detected_objects.append({
                'name': name,
                'conf': round(conf, 2),
                'bbox': [round(x, 1) for x in coords]
            })

        if frame_count % 5 == 0:
            AiVideoService.save_video_detail(video_post_id, frame_count, detected_objects)

        annotated_frame = results[0].plot()
        out.write(annotated_frame)
        frame_count += 1

    cap.release()
    out.release()

    AiVideoService.update_video_status(
        video_post_id, 'COMPLETED',
        f"uploads/ai_detect/{output_filename}",
        total_frames
    )


@app.route('/ai-detect/video/process', methods=['POST'])
def process_video_ai_route():
    if 'video' not in request.files:
        return "<script>alert('파일이 없습니다.'); history.back();</script>"

    file = request.files['video']
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        origin_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ai_detect', filename)
        file.save(origin_path)

        video_post_id = AiVideoService.create_video_post(
            session.get('user_id'),
            request.form.get('title', '제목없음'),
            request.form.get('content', ''),
            f"uploads/ai_detect/{filename}"
        )

        if video_post_id:
            output_filename = f"res_{filename}"
            process_video_ai(video_post_id, origin_path, output_filename)
            return redirect(url_for('view_video', post_id=video_post_id))

    return "<script>alert('분석 실패'); history.back();</script>"


@app.route('/ai-video/view/<int:post_id>')
def view_video(post_id):
    conn = Session.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ai_video_posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()

    cursor.execute(
        "SELECT frame_number, detected_objects FROM ai_video_details WHERE video_post_id = %s ORDER BY frame_number",
        (post_id,))
    details = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('ai_detect/view_video.html', post=post, details=details)

@app.route('/ai-detect/video/delete/<int:post_id>', methods=['POST'])
def ai_video_delete(post_id):
    if session.get('user_role') != 'manager':
        return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"
    
    if AiVideoService.delete_video_post(post_id):
        return "<script>alert('삭제되었습니다.'); location.href='/ai-detect/video';</script>"
    return "<script>alert('삭제 실패'); history.back();</script>"

# ---------------------------------------------------------
# 정적 파일 서빙 및 에러 핸들링
# ---------------------------------------------------------

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("\n" + "=" * 60)
    print("🚀 Aeye Project is Running!")
    print("=" * 60)
    print(f"🔹 [Local]      : http://127.0.0.1:5000")
    print(f"🔹 [Localhost] : http://localhost:5000")
    if local_ip != "127.0.0.1":
        print(f"🔹 [Network]   : http://{local_ip}:5000")
    print("=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
