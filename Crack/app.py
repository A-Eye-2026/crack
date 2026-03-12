import os
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import time
from datetime import datetime
import certifi

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(__file__), 'secrets', '.env'))

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_12345')

# DB 설정
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# TiDB Cloud 연결을 위한 인증서(SSL) 설정 포함 URI
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?ssl_ca={certifi.where()}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 업로드 설정 (최대 500MB)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
UPLOAD_BASE_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
UPLOAD_IMAGE_DIR = os.path.join(UPLOAD_BASE_DIR, 'images')
UPLOAD_VIDEO_DIR = os.path.join(UPLOAD_BASE_DIR, 'videos')

# 디렉토리 자동 생성
for d in [UPLOAD_IMAGE_DIR, UPLOAD_VIDEO_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

db = SQLAlchemy(app)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# 허용된 확장자 확인
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'm4v'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    return redirect(url_for('alert'))

@app.route('/alert')
def alert():
    # 관리자용 AI 신뢰도 0.8 이상 리스트 (임시 데이터)
    alerts = [
        {'id': 1, 'confidence': 0.92, 'location': '서울시 종로구', 'time': '10분 전'},
        {'id': 2, 'confidence': 0.88, 'location': '서울시 강남구', 'time': '30분 전'}
    ]
    return render_template('alert.html', alerts=alerts)

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/status')
def status():
    # 신고 내역 및 공지사항
    reports = [
        {'id': 1, 'title': '포트홀 신고', 'status': '접수완료', 'date': '2024-03-12'},
        {'id': 2, 'title': '도로 파손', 'status': '처리중', 'date': '2024-03-11'}
    ]
    return render_template('status.html', reports=reports)

@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

@app.route('/login')
def login():
    # 임시 로그인 로직 (테스트용)
    session['user_id'] = 1
    session['user_name'] = 'Test User'
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    # 회원가입 페이지 (현재는 인덱스로 리다이렉트)
    return redirect(url_for('index'))

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '선택된 파일이 없습니다.'}), 400
    
    filename = secure_filename(file.filename)
    # 파일명에 타임스탬프 추가하여 중복 방지
    filename = f"{int(time.time())}_{filename}"
    
    if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
        save_path = os.path.join(UPLOAD_IMAGE_DIR, filename)
        file.save(save_path)
        return jsonify({'success': True, 'message': '이미지 업로드 성공', 'path': f'/uploads/images/{filename}'})
    
    elif allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS):
        save_path = os.path.join(UPLOAD_VIDEO_DIR, filename)
        file.save(save_path)
        return jsonify({'success': True, 'message': '동영상 업로드 성공', 'path': f'/uploads/videos/{filename}'})
    
    else:
        return jsonify({'success': False, 'message': '허용되지 않는 파일 형식입니다.'}), 400

@app.route('/api/report', methods=['POST'])
def submit_report():
    title = request.form.get('title')
    content = request.form.get('content')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    file_path = None
    file_type = None

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"
        
        if allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
            save_path = os.path.join(UPLOAD_IMAGE_DIR, filename)
            file.save(save_path)
            file_path = f'/uploads/images/{filename}'
            file_type = 'image'
        elif allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS):
            save_path = os.path.join(UPLOAD_VIDEO_DIR, filename)
            file.save(save_path)
            file_path = f'/uploads/videos/{filename}'
            file_type = 'video'
        else:
            return jsonify({'success': False, 'message': '허용되지 않는 파일 형식입니다. (GIF 동영상 등 확인 요망)'}), 400

    try:
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
    except ValueError:
        lat, lng = None, None

    new_report = Report(
        title=title,
        content=content,
        latitude=lat,
        longitude=lng,
        file_path=file_path,
        file_type=file_type
    )
    db.session.add(new_report)
    db.session.commit()

    return jsonify({'success': True, 'message': '제보가 성공적으로 접수되었습니다.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8888)
