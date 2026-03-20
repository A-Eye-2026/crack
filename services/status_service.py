from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from database import db
from models import Report, CrackTalk, Member
from datetime import timedelta
from utils import check_profanity, get_now_kst

status_bp = Blueprint('status', __name__)

@status_bp.route('/status')
def status():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
        
    one_day_ago = get_now_kst() - timedelta(hours=24)
    # [데이터 관리] 24시간이 지난 반려 게시물은 DB에서 영구 삭제 (사용자 요청 사항)
    expired_rejects = Report.query.filter(
        Report.user_id == user_id,
        Report.status == '반려',
        Report.created_at < one_day_ago
    ).all()
    
    if expired_rejects:
        for r in expired_rejects:
            # 삭제 시 관련 AI 결과도 cascade 등으로 인해 삭제되겠지만 명시적으로 처리 고려 가능
            db.session.delete(r)
        db.session.commit()

    db_reports = Report.query.filter(
        Report.user_id == user_id,
        Report.status != '삭제'
    ).order_by(Report.created_at.desc()).all()
    
    my_reports = []
    for r in db_reports:
        my_reports.append({
            'id': r.id,
            'title': r.title or '제목 없음',
            'status': r.status,
            'date': r.created_at.strftime('%Y-%m-%d') if r.created_at else '',
            'file_path': r.file_path,
            'reject_reason': r.reject_reason
        })
    return render_template('status.html', reports=my_reports)

@status_bp.route('/api/cracktalk', methods=['GET'])
def get_cracktalk():
    # 최근 50개 메시지 조회
    talks = CrackTalk.query.order_by(CrackTalk.created_at.asc()).limit(50).all()
    result = []
    for t in talks:
        result.append({
            'id': t.id,
            'author_id': t.author_id,
            'nickname': t.author.nickname if t.author else '익명',
            'content': t.content,
            'date': t.created_at.strftime('%m-%d %H:%M')
        })
    return jsonify(result)

@status_bp.route('/api/cracktalk', methods=['POST'])
def post_cracktalk():
    from models import PointLog # 순환 참조 방지를 위해 여기서 import
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'message': '내용을 입력해주세요.'}), 400
        
    # 비속어 필터링 적용
    if not check_profanity(content):
        return jsonify({'success': False, 'message': '부적절한 단어가 포함되어 있습니다. 바른 말을 사용해 주세요.'}), 400
        
    user = Member.query.get(user_id)
    # 일반 사용자일 경우 크래커 포인트 20점 차감 (관리자는 무제한)
    if not user.is_admin:
        if user.points < 20:
            return jsonify({'success': False, 'message': '보유한 크래커가 부족합니다. (20 크래커 필요)'}), 400
        user.points -= 20
        db.session.add(PointLog(user_id=user_id, amount=-20, reason='크랙톡 채팅 작성 (포인트 소모)'))
        
    new_talk = CrackTalk(author_id=user_id, content=content)
    db.session.add(new_talk)
    db.session.commit()
    
    return jsonify({'success': True})
