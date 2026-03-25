import os
import time
from datetime import timedelta
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from werkzeug.utils import secure_filename
from database import db
from models import Report, AiResult, Member, PointLog
from utils import allowed_file, extract_gps_from_exif, haversine, reverse_geocode, get_now_kst

report_bp = Blueprint('report', __name__)

# 허용된 확장자 (HEIC/HEIF 추가)
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heic', 'heif'}
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
    
    original_name = file.filename
    print(f"[UPLOAD] Original filename: '{original_name}'")
    
    # [핵심 수정] secure_filename()은 한글 문자를 전부 제거하여 빈 문자열을 만들 수 있음.
    # 예: "안성스타필드.heic" → "" (확장자까지 소멸)
    # 따라서 원본 파일명에서 확장자를 먼저 추출한 뒤, 안전한 이름을 생성합니다.
    import uuid
    original_ext = ''
    if '.' in original_name:
        original_ext = original_name.rsplit('.', 1)[1].lower()
    
    safe_name = secure_filename(original_name)
    
    # secure_filename 결과가 비어있거나 확장자가 없는 경우 UUID 기반 이름 생성
    if not safe_name or '.' not in safe_name:
        safe_name = f"{uuid.uuid4().hex[:12]}.{original_ext}" if original_ext else safe_name
    
    filename = f"{int(time.time())}_{safe_name}"
    print(f"[UPLOAD] Safe filename: '{filename}', Extension: '{original_ext}'")
    
    # 디렉토리 경로 (app.py의 환경설정에 맞춰야 함. 여기선 상대 경로 기준)
    UPLOAD_IMAGE_DIR = os.path.join('uploads', 'images')
    UPLOAD_VIDEO_DIR = os.path.join('uploads', 'videos')

    if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
        save_path = os.path.join(os.getcwd(), UPLOAD_IMAGE_DIR, filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        print(f"[UPLOAD] Image saved to: {save_path} (size: {os.path.getsize(save_path)} bytes)")
        
        # [수정] 업로드 즉시 GPS 메타데이터 추출 (프론트 유실 또는 HEIC 대비 서버 직접 추출)
        lat, lng = extract_gps_from_exif(save_path)
        print(f"[UPLOAD] GPS extraction result: lat={lat}, lng={lng}")
        
        # [NaN 방어] Pillow가 NaN을 반환할 경우 JSON 직렬화 오류 방지
        import math
        if lat is not None and (math.isnan(lat) or math.isinf(lat)):
            lat = None
        if lng is not None and (math.isnan(lng) or math.isinf(lng)):
            lng = None
        
        # GPS가 유효하면 즉시 역지오코딩하여 주소도 반환
        address = None
        if lat and lng:
            from utils import reverse_geocode
            address = reverse_geocode(lat, lng)
            print(f"[UPLOAD] Reverse geocoded address: {address}")
        
        return jsonify({
            'success': True,
            'message': '이미지 업로드 성공 (GPS 추출 시도)',
            'path': f'/uploads/images/{filename}',
            'gps': {'lat': lat, 'lng': lng} if lat and lng else None,
            'address': address
        })
    
    elif allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS):
        save_path = os.path.join(os.getcwd(), UPLOAD_VIDEO_DIR, filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return jsonify({'success': True, 'message': '동영상 업로드 성공', 'path': f'/uploads/videos/{filename}'})
    
    else:
        print(f"[UPLOAD] REJECTED: filename='{filename}', ext='{original_ext}' not in allowed list")
        return jsonify({'success': False, 'message': f'허용되지 않는 파일 형식입니다. (감지된 확장자: {original_ext})'}), 400

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
        import uuid
        original_name = file.filename
        original_ext = ''
        if '.' in original_name:
            original_ext = original_name.rsplit('.', 1)[1].lower()
        safe_name = secure_filename(original_name)
        if not safe_name or '.' not in safe_name:
            safe_name = f"{uuid.uuid4().hex[:12]}.{original_ext}" if original_ext else safe_name
        filename = f"{int(time.time())}_{safe_name}"
        
        UPLOAD_IMAGE_DIR = os.path.join('uploads', 'images')
        UPLOAD_VIDEO_DIR = os.path.join('uploads', 'videos')

        if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
            save_path = os.path.join(os.getcwd(), UPLOAD_IMAGE_DIR, filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            
            # [핵심 수정] 프론트엔드에서 GPS를 이미 전달했는지 확인
            # 크롭된 이미지에는 EXIF가 없으므로 프론트 GPS가 있으면 해당 값을 우선 사용
            front_has_gps = bool(latitude and longitude)
            
            # 프론트에서 GPS를 못 보낸 경우에만 원본 파일에서 EXIF 추출 시도
            if not front_has_gps:
                print(f"[SUBMIT] Frontend didn't provide GPS. Attempting server-side extraction from uploaded file...")
                from utils import extract_gps_from_exif
                exif_lat, exif_lng = extract_gps_from_exif(save_path)
                if exif_lat and exif_lng:
                    latitude = exif_lat
                    longitude = exif_lng
                    print(f"[SUBMIT] ✅ Server-side GPS extraction succeeded: lat={latitude}, lng={longitude}")
                else:
                    print(f"[SUBMIT] ❌ Server-side GPS extraction also failed (file may be cropped/stripped)")
            else:
                print(f"[SUBMIT] ✅ Using GPS from frontend: lat={latitude}, lng={longitude}")
            
            # [개인정보 보호] 모든 이미지의 EXIF 메타데이터를 파기하고 재저장
            try:
                from PIL import Image
                import pillow_heif
                pillow_heif.register_heif_opener()
                
                image = Image.open(save_path)
                
                # 파일 확장자 확인
                file_ext = filename.rsplit('.', 1)[1].lower()
                
                # HEIC/HEIF는 JPG로 변환, 나머지는 유지하되 EXIF 제거
                if file_ext in ['heic', 'heif']:
                    new_filename = filename.rsplit('.', 1)[0] + ".jpg"
                    new_save_path = os.path.join(os.getcwd(), UPLOAD_IMAGE_DIR, new_filename)
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(new_save_path, "JPEG", quality=85)
                    os.remove(save_path)
                    save_path = new_save_path
                    file_path = f'/uploads/images/{new_filename}'
                else:
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(save_path, "JPEG", quality=85)
                    file_path = f'/uploads/images/{filename}'
                
            except Exception as e:
                print(f"Image processing (EXIF Strip) Error: {e}")
                file_path = f'/uploads/images/{filename}'
            
            file_type = 'image'
        elif allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS):
            save_path = os.path.join(os.getcwd(), UPLOAD_VIDEO_DIR, filename)
            file.save(save_path)
            file_path = f'/uploads/videos/{filename}'
            file_type = 'video'
        else:
            return jsonify({'success': False, 'message': '이미지 또는 영상 형식이 올바르지 않습니다.'}), 400

    import math
    try:
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
        if lat is not None and math.isnan(lat): lat = None
        if lng is not None and math.isnan(lng): lng = None
    except (ValueError, TypeError):
        lat, lng = None, None

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
