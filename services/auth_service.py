import os
import json
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import Member
from utils import check_profanity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Member.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.nickname if user.nickname else user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="아이디 또는 비밀번호가 잘못되었습니다.")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        nickname = request.form.get('nickname')
        
        # 닉네임 정책 검증 (20자 제한 + 비속어 필터링)
        if not nickname or len(nickname) > 20:
            return render_template('signup.html', error="닉네임은 1자 이상 20자 이하로 입력해주세요.")
            
        if not check_profanity(nickname):
            return render_template('signup.html', error="닉네임에 부적절한 단어가 포함되어 있습니다. 바른 말을 사용해 주세요.")

        if Member.query.filter_by(username=username).first():
            return render_template('signup.html', error="이미 존재하는 아이디입니다.")
            
        hashed_pw = generate_password_hash(password)
        new_user = Member(username=username, password_hash=hashed_pw, nickname=nickname, points=100)
        db.session.add(new_user)
        db.session.commit()
        
        # 가입 축하 포인트 로그 추가
        from models import PointLog
        db.session.add(PointLog(user_id=new_user.id, amount=100, reason='신규 가입 축하 포인트'))
        db.session.commit()
        
        return redirect(url_for('auth.login'))
        
    return render_template('signup.html')

@auth_bp.route('/api/check_id', methods=['POST'])
def check_id():
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'available': False, 'message': '아이디를 입력해주세요.'}), 400
        
    user = Member.query.filter_by(username=username).first()
    if user:
        return jsonify({'available': False, 'message': '이미 존재하는 아이디입니다.'})
    else:
        return jsonify({'available': True, 'message': '사용 가능한 아이디입니다.'})
