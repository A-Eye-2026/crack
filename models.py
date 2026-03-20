from database import db
from utils import get_now_kst

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(80), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    points = db.Column(db.Integer, default=0) # 크래커 포인트
    created_at = db.Column(db.DateTime, default=get_now_kst)

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='담당자 확인중')
    reject_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=get_now_kst)
    author = db.relationship('Member', backref=db.backref('reports', lazy=True))

class AiResult(db.Model):
    __tablename__ = 'ai_results'
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id', ondelete='CASCADE'), nullable=False)
    is_damaged = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float, nullable=True)
    damage_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=get_now_kst)
    report = db.relationship('Report', backref=db.backref('ai_result', uselist=False, cascade='all, delete-orphan'))

class PointLog(db.Model):
    __tablename__ = 'point_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=get_now_kst)
    member = db.relationship('Member', backref=db.backref('point_logs', lazy=True, order_by='PointLog.created_at.desc()'))

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), nullable=False, unique=True)
    notification_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_now_kst)
    member = db.relationship('Member', backref=db.backref('settings', uselist=False))

class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='시스템')
    author_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=get_now_kst)
    created_at = db.Column(db.DateTime, default=get_now_kst)
    author = db.relationship('Member', backref=db.backref('notices', lazy=True))

class CrackTalk(db.Model):
    __tablename__ = 'crack_talk'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_now_kst)
    
    # Relationship
    author = db.relationship('Member', backref=db.backref('crack_talks', lazy=True, order_by='CrackTalk.created_at.asc()'))
