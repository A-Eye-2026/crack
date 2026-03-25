import os
import certifi
import threading
import math
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask, render_template, session, redirect, url_for, send_from_directory, make_response, request, jsonify
from dotenv import load_dotenv
from ultralytics import YOLO
import cv2

# 내부 모듈 임포트
from database import db
from models import Report, AiResult, Member, VideoDetection
from utils import reverse_geocode

# 서비스 Blueprint 임포트
from services.auth_service import auth_bp
from services.alert_service import alert_bp
from services.report_service import report_bp
from services.status_service import status_bp
from services.my_service import my_bp

# .env 파일 로드 (secrets 폴더 확인)
base_dir = os.path.dirname(__file__)
env_path = os.path.join(base_dir, 'secrets', '.env')

if not os.path.exists(env_path):
    print("\n" + "!"*50)
    print("⚠️  CRITICAL ERROR: 'secrets/.env' FILE NOT FOUND!")
    print("팀원들은 'secrets.example' 폴더의 내용을 참고하여 'secrets' 폴더를 생성하고")
    print("필요한 설정 파일들을 직접 만들어야 합니다.")
    print("!"*50 + "\n")
else:
    load_dotenv(env_path)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_12345')

# DB 설정 (TiDB Cloud 연결 지원)
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME')

if not all([db_user, db_password, db_host, db_name]):
    print("⚠️  Warning: Database environment variables are missing.")
    # 기본값 설정을 통해 최소한의 구성은 유지하거나 에러 처리 필요
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temp_debug.db'
else:
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
# app.py 60~62라인쯤에 추가
print("DEBUG: SQLALCHEMY_DATABASE_URI =", app.config.get('SQLALCHEMY_DATABASE_URI'))

db.init_app(app) # 63라인


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

@app.route('/api/admin/reanalyze/<int:report_id>', methods=['POST'])
def admin_reanalyze(report_id):
    """지정된 제보에 대해 AI 재분석을 실행합니다."""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
    
    try:
        rpt = Report.query.get_or_404(report_id)
        
        # 1. 기존 분석 결과물 삭제
        AiResult.query.filter_by(report_id=report_id).delete()
        VideoDetection.query.filter_by(report_id=report_id).delete()
        
        # 2. 상태 변경
        rpt.status = 'AI 분석중'
        db.session.commit()
        
        # 3. 비동기 분석 시작
        thread = threading.Thread(target=run_ai_analysis, args=(rpt.id, rpt.file_path, rpt.file_type))
        thread.start()
        
        return jsonify({'success': True, 'message': 'AI 재분석이 성공적으로 시작되었습니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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

# --- 대시보드 고도화 유틸리티 함수 --- #

def normalize_region_name(region_text):
    if not region_text: return ''
    text = region_text.strip()
    parts = text.split()
    if len(parts) >= 2:
        first, second = parts[0], parts[1]
        if first.endswith('시') and (second.endswith('구') or second.endswith('군') or second.endswith('시')):
            return f"{first} {second}"
    return parts[0] if len(parts) >= 1 else ''

def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000  # meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

def get_priority_score(report, now=None):
    if now is None: now = datetime.now()
    score = 0
    # AI 신뢰도를 위험 점수로 활용 (None 방어 코드)
    confidence = float(report.ai_result.confidence or 0) if report.ai_result else 0
    status = report.status
    created_at = report.created_at

    if status == '관리자 확인중': score += 100
    if confidence >= 80: score += 50
    elif confidence >= 50: score += 20
    
    # 반복 제보(그룹화 시 계산됨) - 여기서는 기본 점수만
    if status == '관리자 확인중' and created_at and (now - created_at).total_seconds() >= 86400:
        score += 40
    return score

def get_priority_label(score):
    if score >= 150: return '긴급'
    elif score >= 80: return '주의'
    return '일반'

def group_reports(raw_reports):
    grouped = []
    used_ids = set()
    for r in raw_reports:
        if r.id in used_ids: continue
        group_members = [r]
        used_ids.add(r.id)
        reporter_ids = {r.user_id}
        
        for other in raw_reports:
            if other.id == r.id or other.id in used_ids: continue
            if r.latitude is None or r.longitude is None or other.latitude is None or other.longitude is None: continue
            
            distance = haversine_m(r.latitude, r.longitude, other.latitude, other.longitude)
            time_diff = abs((r.created_at - other.created_at).total_seconds())
            
            if distance <= 50 and time_diff <= 86400:
                used_ids.add(other.id)
                group_members.append(other)
                if other.user_id: reporter_ids.add(other.user_id)
        
        # 대표 리포트 선정 (가장 높은 신뢰도 기준)
        representative = max(group_members, key=lambda x: (x.ai_result.confidence if x.ai_result else 0, x.created_at.timestamp()))
        representative.group_count = len(group_members)
        representative.reporter_count = len(reporter_ids)
        representative.members = group_members
        grouped.append(representative)
    return grouped

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    selected_tab = request.args.get('tab', 'pending')
    now = datetime.now()
    today = now.date()
    
    # 모든 리포트 가져오기 (성능 최적화를 위해 AI 결과와 함께 로드)
    from sqlalchemy.orm import joinedload
    reports = Report.query.options(joinedload(Report.ai_result)).order_by(Report.created_at.desc()).all()
    
    # 지능형 그룹화 적용
    grouped_reports = group_reports(reports)
    
    # 통계 계산
    summary = {
        "urgent_count": 0,
        "today_count": sum(1 for r in grouped_reports if r.created_at.date() == today and r.status != '반려'),
        "pending_count": sum(1 for r in grouped_reports if r.status == '관리자 확인중'),
        "processing_count": sum(1 for r in grouped_reports if r.status in ['접수완료', '처리중']),
        "long_pending_count": sum(1 for r in grouped_reports if r.status == '관리자 확인중' and (now - r.created_at).total_seconds() >= 86400),
        "rejected_count": sum(1 for r in grouped_reports if r.status == '반려')
    }
    
    for r in grouped_reports:
        score = get_priority_score(r, now)
        r.priority_score = score
        r.priority_label = get_priority_label(score)
        if r.status in ['관리자 확인중', '처리중'] and r.priority_label == '긴급':
            summary['urgent_count'] += 1

    # 탭별 필터링 및 섹션 정보 설정
    display_list = []
    section_title = "전체 신고 목록"
    section_subtitle = "시스템에 접수된 모든 신고 내역입니다."
    
    if selected_tab == 'urgent':
        display_list = [r for r in grouped_reports if (r.status in ['관리자 확인중', '처리중'] and r.priority_label == '긴급')]
        section_title = f"긴급 조치 대상 ({len(display_list)}건)"
        section_subtitle = "위험도가 높거나 반복 신고된 긴급 관리 대상입니다."
    elif selected_tab == 'today':
        display_list = [r for r in grouped_reports if r.created_at.date() == today and r.status != '반려']
        section_title = f"오늘 접수된 신고 ({len(display_list)}건)"
        section_subtitle = f"{today.strftime('%Y-%m-%d')} 기준 신규 신고 내역입니다. (반려 건은 반려 내역 탭으로 자동 이동)"
    elif selected_tab == 'pending':
        display_list = [r for r in grouped_reports if r.status == '관리자 확인중']
        section_title = f"미처리 신고 ({len(display_list)}건)"
        section_subtitle = "아직 관리자가 확인하지 않은 대기 중인 신고입니다."
    elif selected_tab == 'processing':
        display_list = [r for r in grouped_reports if r.status in ['접수완료', '처리중']]
        section_title = f"처리 진행 중 ({len(display_list)}건)"
        section_subtitle = "접수 완료되어 현재 보수 및 후속 조치가 진행 중인 내역입니다."
    elif selected_tab == 'long_pending':
        display_list = [r for r in grouped_reports if r.status == '관리자 확인중' and (now - r.created_at).total_seconds() >= 86400]
        section_title = f"장기 미처리 신고 ({len(display_list)}건)"
        section_subtitle = "접수 후 24시간이 경과한 우선 처리 요망 건입니다."
    elif selected_tab == 'rejected':
        display_list = [r for r in grouped_reports if r.status == '반려']
        section_title = f"반려된 신고 ({len(display_list)}건)"
        section_subtitle = "관리 기준 미달 또는 중복으로 반려된 내역입니다."
    else:
        display_list = grouped_reports

    # 리포트 객체에 urgent_reason 속성 추가 (템플릿 호환용)
    for r in display_list:
        reasons = []
        if (float(r.ai_result.confidence or 0) if r.ai_result else 0) >= 80: reasons.append('고위험')
        if getattr(r, 'reporter_count', 1) >= 3: reasons.append('반복 제보')
        if r.status == '관리자 확인중' and (now - r.created_at).total_seconds() >= 86400: reasons.append('장기 미처리')
        # 반려된 신고일 경우 적절한 텍스트 표시
        if r.status == '반려':
            reasons.append('반려 처분')
        r.urgent_reason = ', '.join(reasons) if reasons else ''
        r.group_reporter_count = getattr(r, 'reporter_count', 1)

    # 지역별 통계
    region_stats = {}
    for r in grouped_reports:
        region = normalize_region_name(r.address) or '기타'
        if region not in region_stats:
            region_stats[region] = {'total': 0, 'pending': 0, 'done': 0, 'rejected': 0}
        region_stats[region]['total'] += 1
        if r.status == '관리자 확인중': region_stats[region]['pending'] += 1
        elif r.status == '처리완료': region_stats[region]['done'] += 1
        elif r.status == '반려': region_stats[region]['rejected'] += 1
    
    region_stats_list = sorted([{'region': k, **v} for k, v in region_stats.items()], key=lambda x: x['pending'], reverse=True)

    # 지도 핀용 전체 리포트 좌표 데이터
    map_pins = []
    for r in grouped_reports:
        if r.latitude and r.longitude:
            map_pins.append({
                'id': r.id,
                'lat': float(r.latitude),
                'lng': float(r.longitude),
                'status': r.status or '관리자 확인중',
                'address': r.address or '주소 없음',
                'confidence': float(r.ai_result.confidence or 0) if r.ai_result else 0
            })

    return render_template('admin_dashboard.html', 
                           dashboard_items=display_list, 
                           summary=summary, 
                           region_stats=region_stats_list,
                           selected_tab=selected_tab,
                           dashboard_section_title=section_title,
                           dashboard_section_subtitle=section_subtitle,
                           dashboard_more_url=url_for('status.status'),
                           map_pins=map_pins)


@app.route('/admin/report/update-status', methods=['POST'])
def update_report_status():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
    
    report_id = request.form.get('report_id')
    new_status = request.form.get('status')
    reject_reason = request.form.get('reject_reason', '')
    sync_group = request.form.get('sync_group') == 'true'
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'message': '신고를 찾을 수 없습니다.'}), 404
    
    target_ids = [report.id]
    if sync_group:
        # 같은 그룹(50m, 24h)의 다른 신고들도 찾음
        all_reports = Report.query.all()
        for r in all_reports:
            if r.id == report.id: continue
            if report.latitude and report.longitude and r.latitude and r.longitude:
                if haversine_m(report.latitude, report.longitude, r.latitude, r.longitude) <= 50 and \
                   abs((report.created_at - r.created_at).total_seconds()) <= 86400:
                    target_ids.append(r.id)
    
    # 상태 업데이트
    from models import PointLog
    for tid in target_ids:
        r = Report.query.get(tid)
        r.status = new_status
        if new_status == '반려':
            r.reject_reason = reject_reason
        else:
            r.reject_reason = None
            
        # 처리 완료 시 포인트 지급 (중복 지급 방지 로직 필요시 추가)
        if new_status == '처리완료':
            mbr = Member.query.get(r.user_id)
            if mbr:
                mbr.points += 50 # 처리 완료 보상
                db.session.add(PointLog(user_id=r.user_id, amount=50, reason='도로 파손 보수 완료 보상'))
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/reanalyze/<int:report_id>', methods=['POST'])
def reanalyze_report(report_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'message': '신고를 찾을 수 없습니다.'}), 404
        
    try:
        # 기존 AI 결과 및 비디오 검출 데이터 삭제
        from models import AiResult, VideoDetection
        AiResult.query.filter_by(report_id=report_id).delete()
        VideoDetection.query.filter_by(report_id=report_id).delete()
        db.session.commit()
        
        # 새로운 스레드에서 분석 시작
        threading.Thread(target=run_ai_analysis, args=(report.id, report.file_path, report.file_type)).start()
        
        return jsonify({'success': True, 'message': 'AI 재분석을 시작했습니다. 잠시 후 새로고침 해주세요.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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
        is_damaged, max_conf, pothole_count, pothole_max_conf, damage_type = False, 0.0, 0, 0.0, "없음"
        annotated_path = None

        if file_type == 'video':
            # === 동영상 분석: 프레임 추출 후 YOLO 분석 및 박스 오버레이 인코딩 ===
            print(f"[AI Video] Starting video analysis: {abs_path}")
            cap = cv2.VideoCapture(abs_path)
            if not cap.isOpened():
                print(f"[AI Video] ERROR: Cannot open video file")
                return
            
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 출력 파일 설정 (H.264 코덱 사용)
            name, ext = os.path.splitext(os.path.basename(abs_path))
            output_filename = f"res_{name}.mp4"
            output_abs_path = os.path.join(os.path.dirname(abs_path), output_filename)
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(output_abs_path, fourcc, fps, (width, height))
            
            best_frame = None
            best_result = None
            best_conf = 0.0
            frame_idx = 0
            frame_detections = [] 
            
            sample_interval = max(int(fps // 5), 1)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_h, frame_w = frame.shape[:2]
                current_time_sec = frame_idx / fps
                
                results = model(frame, verbose=False)
                # 현재 프레임에 CV 박스 그리기
                annotated_frame = results[0].plot()
                out.write(annotated_frame)
                
                # DB 저장용 데이터 추출 (초당 약 5번만 기록)
                if frame_idx % sample_interval == 0:
                    for r in results:
                        if len(r.boxes) > 0:
                            for box in r.boxes:
                                cls_name = r.names[int(box.cls[0])]
                                conf = float(box.conf[0])
                                xyxy = box.xyxy[0].tolist()
                                nx1, ny1, nx2, ny2 = xyxy[0]/frame_w, xyxy[1]/frame_h, xyxy[2]/frame_w, xyxy[3]/frame_h
                                
                                frame_detections.append({
                                    'frame_time': round(current_time_sec, 2),
                                    'class_name': cls_name,
                                    'confidence': round(conf, 4),
                                    'x1': round(nx1, 4), 'y1': round(ny1, 4),
                                    'x2': round(nx2, 4), 'y2': round(ny2, 4)
                                })
                                
                                if 'pothole' in cls_name.lower():
                                    is_damaged = True
                                    pothole_count += 1
                                    if conf > pothole_max_conf:
                                        pothole_max_conf = conf
                                if conf > max_conf:
                                    max_conf, damage_type = conf, cls_name
                                if conf > best_conf:
                                    best_conf = conf
                                    best_frame = frame.copy()
                                    best_result = results[0]

                frame_idx += 1
                # 혹시 너무 길어지는걸 방지하기 위해 1.5분(2700프레임) 단위로 자르기
                if frame_idx >= 2700:
                    break
            
            cap.release()
            out.release()
            print(f"[AI Video] Analyzed {frame_idx} frames. Detections={len(frame_detections)}, Pothole={pothole_count}")
            print(f"[AI Video] Output video saved to {output_abs_path}")
            
            encoded_video_path = f'/uploads/videos/{output_filename}'
            
            # 프레임별 검출 결과를 DB에 일괄 저장
            if frame_detections:
                with app.app_context():
                    from models import VideoDetection
                    for det in frame_detections:
                        db.session.add(VideoDetection(
                            report_id=report_id,
                            frame_time=det['frame_time'],
                            class_name=det['class_name'],
                            confidence=det['confidence'],
                            x1=det['x1'], y1=det['y1'],
                            x2=det['x2'], y2=det['y2']
                        ))
                    db.session.commit()
                    print(f"[AI Video] Saved {len(frame_detections)} detections to DB")
            
            # 가장 높은 신뢰도 프레임을 AI 결과 썸네일로 저장
            if best_result is not None and best_frame is not None:
                annotated_filename = f"{name}_ai.jpg"
                annotated_abs = os.path.join(base_dir, 'uploads', 'images', annotated_filename)
                os.makedirs(os.path.dirname(annotated_abs), exist_ok=True)
                cv2.imwrite(annotated_abs, best_result.plot())
                annotated_path = f'/uploads/images/{annotated_filename}'
                print(f"[AI Video] Best frame saved: {annotated_path}")
        
        else:
            # === 이미지 분석 (기존 로직) ===
            results = model(abs_path, verbose=False)
            
            for r in results:
                if len(r.boxes) > 0:
                    for box in r.boxes:
                        cls_name = r.names[int(box.cls[0])]
                        conf = float(box.conf[0])
                        if 'pothole' in cls_name.lower():
                            is_damaged, pothole_count = True, pothole_count + 1
                            if conf > pothole_max_conf: pothole_max_conf = conf
                        if conf > max_conf: max_conf, damage_type = conf, cls_name
            
            if (is_damaged or (len(results) > 0 and len(results[0].boxes) > 0)):
                name = os.path.splitext(os.path.basename(abs_path))[0]
                annotated_filename = f"{name}_ai.jpg"
                annotated_abs = os.path.join(os.path.dirname(abs_path), annotated_filename)
                cv2.imwrite(annotated_abs, results[0].plot())
                annotated_path = f'/uploads/images/{annotated_filename}'

        with app.app_context():
            rpt = Report.query.get(report_id)
            if rpt:
                db.session.add(AiResult(report_id=report_id, is_damaged=is_damaged, confidence=round(max_conf * 100, 1), damage_type=damage_type))
                if annotated_path:
                    rpt.thumbnail_path = annotated_path # 원본 경로는 보존하되 새로 갱신
                
                # 핵심: CV 박스가 그려져 재인코딩된 영상이 있다면 원본을 덮어써서 프론트에서 재생하게 함
                if file_type == 'video' and 'encoded_video_path' in locals():
                    rpt.file_path = encoded_video_path
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
