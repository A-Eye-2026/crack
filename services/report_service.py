import os
import time
from datetime import timedelta
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from werkzeug.utils import secure_filename
from database import db
from models import Report, AiResult, Member, PointLog
from utils import allowed_file, extract_gps_from_exif, haversine, reverse_geocode, get_now_kst

report_bp = Blueprint('report', __name__)

# 허용된 확장자 (utils.py에서 가져오거나 여기서 정의)
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'm4v'}

@report_bp.route('/report', methods=['GET'])
def report_page():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    # kakao_js_key는 context_processor에 의해 주입됨
    return render_template('report.html')

@report_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '선택된 파일이 없습니다.'}), 400
    
    filename = secure_filename(file.filename)
    filename = f"{int(time.time())}_{filename}"
    
    # 디렉토리 경로 (app.py의 환경설정에 맞춰야 함. 여기선 상대 경로 기준)
    UPLOAD_IMAGE_DIR = os.path.join('uploads', 'images')
    UPLOAD_VIDEO_DIR = os.path.join('uploads', 'videos')

    if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
        save_path = os.path.join(os.getcwd(), UPLOAD_IMAGE_DIR, filename)
        file.save(save_path)
        return jsonify({'success': True, 'message': '이미지 업로드 성공', 'path': f'/uploads/images/{filename}'})
    
    elif allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS):
        save_path = os.path.join(os.getcwd(), UPLOAD_VIDEO_DIR, filename)
        file.save(save_path)
        return jsonify({'success': True, 'message': '동영상 업로드 성공', 'path': f'/uploads/videos/{filename}'})
    
    else:
        return jsonify({'success': False, 'message': '허용되지 않는 파일 형식입니다.'}), 400

@report_bp.route('/api/report', methods=['POST'])
def submit_report():
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': '제보를 위해 로그인이 필요합니다.'}), 401
        
    user_id = session.get('user_id')
    title = request.form.get('title', '')[:30]
    content = request.form.get('content')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    address = request.form.get('address')
    
    file_path = None
    file_type = None

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"
        
        UPLOAD_IMAGE_DIR = os.path.join('uploads', 'images')
        UPLOAD_VIDEO_DIR = os.path.join('uploads', 'videos')

        if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
            save_path = os.path.join(os.getcwd(), UPLOAD_IMAGE_DIR, filename)
            file.save(save_path)
            file_path = f'/uploads/images/{filename}'
            file_type = 'image'
        elif allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS):
            save_path = os.path.join(os.getcwd(), UPLOAD_VIDEO_DIR, filename)
            file.save(save_path)
            file_path = f'/uploads/videos/{filename}'
            file_type = 'video'

    try:
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
    except ValueError:
        lat, lng = None, None

    if file_type == 'image' and file_path and (lat is None or lng is None):
        abs_img = os.path.join(os.getcwd(), file_path.lstrip('/'))
        exif_lat, exif_lng = extract_gps_from_exif(abs_img)
        if exif_lat and exif_lng:
            lat, lng = exif_lat, exif_lng

    if lat and lng and not address:
        address = reverse_geocode(lat, lng)

    # 중복 신고 제한
    if lat and lng:
        yesterday = get_now_kst() - timedelta(hours=24)
        duplicate = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= yesterday,
            Report.latitude.isnot(None),
            Report.longitude.isnot(None)
        ).all()
        for r in duplicate:
            if haversine(lat, lng, r.latitude, r.longitude) <= 50:
                return jsonify({'success': False, 'message': '이미 1일 내 반경 50m 이내에 신고하신 건이 있습니다.'}), 400

    new_report = Report(
        user_id=user_id,
        title=title,
        content=content,
        latitude=lat,
        longitude=lng,
        address=address,
        file_path=file_path,
        file_type=file_type,
        status='AI 분석중'
    )
    db.session.add(new_report)
    db.session.commit()

    # 크래커 포인트 적립 (신고 접수 +10점)
    member = Member.query.get(user_id)
    if member:
        member.points += 10
        db.session.add(PointLog(user_id=user_id, amount=10, reason='신고 접수'))
        db.session.commit()
    
    # AI 분석 트리거 (app.py의 전역 함수를 호출하거나, 패키지 간 순환 참조 방지를 고려해야 함)
    # 여기서는 post_report_hook 스크립트를 생성하거나 app.py의 함수를 임포트하여 비동기 실행
    from flask import current_app
    if hasattr(current_app, 'run_ai_analysis'):
        import threading
        thread = threading.Thread(target=current_app.run_ai_analysis, args=(new_report.id, file_path, file_type))
        thread.start()

    return jsonify({'success': True, 'message': '제보가 성공적으로 접수되어 AI 분석을 시작합니다.', 'report_id': new_report.id})

@report_bp.route('/api/report/status/<int:report_id>', methods=['GET'])
def get_report_status(report_id):
    rpt = Report.query.get_or_404(report_id)
    return jsonify({
        'status': rpt.status,
        'is_analyzing': rpt.status == 'AI 분석중'
    })
