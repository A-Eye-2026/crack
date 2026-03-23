import os
import certifi
import threading
from flask import Flask, render_template, session, redirect, url_for, send_from_directory, make_response
from dotenv import load_dotenv
from ultralytics import YOLO
import cv2

# 내부 모듈 임포트
from database import db
from models import Report, AiResult, Member
from utils import reverse_geocode

# 서비스 Blueprint 임포트
from services.auth_service import auth_bp
from services.alert_service import alert_bp
from services.report_service import report_bp
from services.status_service import status_bp
from services.my_service import my_bp

# .env 파일 로드
base_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(base_dir, 'secrets', '.env'))

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_12345')

# DB 설정 (TiDB Cloud 연결 지원)
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?ssl_ca={certifi.where()}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True, 
    'pool_recycle': 3600,
    'connect_args': {
        'init_command': "SET time_zone = '+09:00'"
    }
}

# 업로드 설정 (최대 100MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
UPLOAD_BASE_DIR = os.path.join(base_dir, 'uploads')
UPLOAD_IMAGE_DIR = os.path.join(UPLOAD_BASE_DIR, 'images')
UPLOAD_VIDEO_DIR = os.path.join(UPLOAD_BASE_DIR, 'videos')

# 디렉토리 생성
for d in [UPLOAD_IMAGE_DIR, UPLOAD_VIDEO_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# DB 초기화
db.init_app(app)

# AI 모델 로드
try:
    model_path = os.path.join(base_dir, 'static', 'best.pt')
    model = YOLO(model_path)
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

# Blueprint 등록
app.register_blueprint(auth_bp)
app.register_blueprint(alert_bp)
app.register_blueprint(report_bp)
app.register_blueprint(status_bp)
app.register_blueprint(my_bp)

# --- 공통 기능 및 API 설정 --- #

# 카카오 JS 키 로드 및 주입
kakao_js_key = ""
try:
    with open(os.path.join(base_dir, 'secrets', 'kakao_js_key.txt'), 'r', encoding='utf-8') as f:
        kakao_js_key = f.read().strip()
except Exception as e:
    print(f"Error loading kakao js key: {e}")

@app.context_processor
def inject_global_vars():
    """모든 템플릿에서 쓸 수 있는 전역 변수 주입"""
    admin_unread_count = 0
    if session.get('is_admin'):
        admin_unread_count = Report.query.filter_by(status='관리자 확인중').count()
    return dict(kakao_js_key=kakao_js_key, admin_unread_count=admin_unread_count)

# 정적 파일 서빙
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    response = make_response(send_from_directory('static', 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_BASE_DIR, filename)

# 메인 및 공통 라우트
@app.route('/')
def index():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    # [보정] 세션 어드민 권한 동기화 (DB 상태와 세션 불일치 해결)
    user = Member.query.get(session['user_id'])
    if user:
        session['is_admin'] = user.is_admin
        
    return render_template('index.html')

@app.route('/login_page')
def login_page():
    return redirect(url_for('auth.login'))

@app.route('/map-test')
def map_test():
    return render_template('map_test.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    return render_template('admin_dashboard.html')

@app.route('/admin/ppt')
def admin_ppt():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    return render_template('ppt.html')

# AI 분석 함수 (Thread용 공통 기능)
def run_ai_analysis(report_id, file_path, file_type):
    if not model: return
    abs_path = os.path.join(base_dir, file_path.lstrip('/'))
    try:
        results = model(abs_path, verbose=False)
        is_damaged, max_conf, pothole_count, pothole_max_conf, damage_type = False, 0.0, 0, 0.0, "없음"
        
        for r in results:
            if len(r.boxes) > 0:
                for box in r.boxes:
                    cls_name = r.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    # 클래스 명칭에 'pothole'이 포함되어 있으면 포트홀로 인식 (예: Pothole_Damage)
                    if 'pothole' in cls_name.lower():
                        is_damaged, pothole_count = True, pothole_count + 1
                        if conf > pothole_max_conf: pothole_max_conf = conf
                    if conf > max_conf: max_conf, damage_type = conf, cls_name
        
        annotated_path = None
        if (is_damaged or (len(results) > 0 and len(results[0].boxes) > 0)) and file_type == 'image':
            name = os.path.splitext(os.path.basename(abs_path))[0]
            # [수정] 확장자를 항상 .jpg로 하여 OpenCV 호환성 확보 및 브라우저 지원 보장
            annotated_filename = f"{name}_ai.jpg"
            annotated_abs = os.path.join(os.path.dirname(abs_path), annotated_filename)
            cv2.imwrite(annotated_abs, results[0].plot())
            annotated_path = f'/uploads/images/{annotated_filename}'

        with app.app_context():
            rpt = Report.query.get(report_id)
            if rpt:
                db.session.add(AiResult(report_id=report_id, is_damaged=is_damaged, confidence=round(max_conf * 100, 1), damage_type=damage_type))
                if annotated_path:
                    rpt.file_path = annotated_path
                # AI 분석 승인 조건: 포트홀이 1개라도 있고(pothole_count > 0) 최대 신뢰도가 60% 이상인 경우
                if pothole_count > 0 and pothole_max_conf >= 0.6:
                    rpt.status = '관리자 확인중'
                    # AI 분석 통과 보상 (+10점)
                    from models import PointLog
                    mbr = Member.query.get(rpt.user_id)
                    if mbr:
                        mbr.points += 10
                        db.session.add(PointLog(user_id=rpt.user_id, amount=10, reason='AI 분석 통과 (유효한 제보)'))
                else:
                    rpt.status = '반려'
                    if pothole_count == 0:
                        rpt.reject_reason = 'AI 분석 결과 도로 파손(포트홀)이 감지되지 않았습니다. 다시 정확하게 촬영해주세요.'
                    else:
                        rpt.reject_reason = 'AI 분석 결과 신뢰도가 낮습니다(60% 미만). 더 가까이서 명확하게 촬영해주세요.'
                db.session.commit()
    except Exception as e:
        print(f"AI Analysis Error: {e}")

# current_app을 통해 접근 가능하도록 바인딩
app.run_ai_analysis = run_ai_analysis

# 서버 실행부
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # 포트 8012 유지
    print("\n" + "="*50)
    print("🚀  CRACK SERVER v1.2.8  READY")
    print("📈  Smart Road Safety Platform")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=8012, debug=True)
