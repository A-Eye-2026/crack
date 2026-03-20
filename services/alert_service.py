from flask import Blueprint, render_template, session, request, jsonify
from database import db
from models import Report, AiResult, Member, Notice, PointLog
from utils import haversine, get_now_kst
from datetime import timedelta
import re

alert_bp = Blueprint('alert', __name__)

@alert_bp.route('/alert')
def alert():
    is_admin = session.get('is_admin', False)
    
    one_day_ago = get_now_kst() - timedelta(hours=24)
    # 1. 1차 전체 유효 데이터 로드
    if is_admin:
        alerts_query = Report.query.filter(
            Report.status != '삭제',
            Report.status != 'AI 분석중',
            db.or_(
                Report.status != '반려',
                Report.created_at >= one_day_ago
            )
        ).order_by(
            db.case((Report.status == '반려', 2), else_=1),
            Report.created_at.desc()
        ).all()
    else:
        user_id = session.get('user_id')
        # 일반 사용자는 '반려', '삭제', '관리자 확인중', '담당자 확인중', 'AI 분석중' 상태를 피드에서 볼 수 없음
        alerts_query = Report.query.join(AiResult, Report.id == AiResult.report_id, isouter=True).filter(
            db.or_(
                Report.user_id == user_id,
                AiResult.id.isnot(None)
            ),
            Report.status.notin_(['삭제', 'AI 분석중', '반려', '관리자 확인중', '담당자 확인중'])
        ).order_by(Report.created_at.desc()).all()
    
    # 2. 클러스터링 및 그룹 생성
    grouped_alerts = []
    used_ids = set()

    for rpt in alerts_query:
        if rpt.id in used_ids:
            continue
            
        base_lat = rpt.latitude
        base_lng = rpt.longitude
        base_title = rpt.title or ''
        base_time = rpt.created_at
        reporter_ids = set()
        
        if rpt.user_id:
            reporter_ids.add(rpt.user_id)
            
        for other in alerts_query:
            if other.id in used_ids or other.id == rpt.id:
                continue
                
            other_title = other.title or ''
            other_time = other.created_at
            
            if not base_lat or not base_lng or not other.latitude or not other.longitude:
                continue

            distance_m = haversine(base_lat, base_lng, other.latitude, other.longitude)
            time_diff_sec = abs((base_time - other_time).total_seconds()) if base_time and other_time else 999999
            
            if distance_m <= 500 and time_diff_sec <= 3600 and base_title == other_title:
                used_ids.add(other.id)
                if other.user_id:
                    reporter_ids.add(other.user_id)
        
        rpt_dict = {
            'report': rpt,
            'group_reporter_count': len(reporter_ids)
        }
        grouped_alerts.append(rpt_dict)
        used_ids.add(rpt.id)
        
    # 3. 위험도 기반 노출 필터 및 최종 데이터 포맷팅
    alerts_result = []
    for item in grouped_alerts:
        rpt = item['report']
        reporter_count = item['group_reporter_count']
        
        ai_res = AiResult.query.filter_by(report_id=rpt.id).first()
        confidence = float(ai_res.confidence) if ai_res and ai_res.confidence else 0.0
        damage_type = ai_res.damage_type if ai_res else 'N/A'

        if not is_admin:
            if rpt.user_id != session.get('user_id'):
                visible_to_user = (confidence >= 60 or (confidence >= 50 and reporter_count >= 3))
                if not visible_to_user:
                    continue

        simplified_address = rpt.address
        if rpt.address:
            match = re.search(r'([가-힣]+[시도])\s+([가-힣]+[구군시])\s+([가-힣0-9]+[로길])', rpt.address)
            if match:
                simplified_address = match.group(0)

        reporter = Member.query.get(rpt.user_id)
        reporter_name = reporter.nickname if reporter and reporter.nickname else (reporter.username if reporter else '알 수 없음')

        alerts_result.append({
            'id': rpt.id,
            'report_id': rpt.id,
            'confidence': confidence,
            'damage_type': damage_type,
            'status': rpt.status,
            'title': rpt.title or '도로 파손 신고',
            'location': f'{rpt.latitude:.4f}, {rpt.longitude:.4f}' if rpt.latitude else '위치 정보 없음',
            'address': simplified_address,
            'full_address': rpt.address,
            'time': rpt.created_at.strftime('%Y-%m-%d %H:%M:%S') if rpt.created_at else '알 수 없음',
            'file_path': rpt.file_path,
            'file_type': rpt.file_type,
            'lat': rpt.latitude,
            'lng': rpt.longitude,
            'reporter_name': reporter_name,
            'reporter_count': reporter_count
        })

    notices_query = Notice.query.order_by(Notice.created_at.desc()).all()
    notices = []
    for n in notices_query:
        notices.append({
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'category': n.category,
            'date': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'author': n.author.nickname or n.author.username if n.author else '관리자'
        })
        
    return render_template('alert.html', alerts=alerts_result, notices=notices, is_admin=is_admin)

@alert_bp.route('/api/admin/report/<int:report_id>/status', methods=['POST'])
def update_report_status(report_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({'success': False, 'message': '상태 값이 누락되었습니다.'}), 400
        
    try:
        rpt = Report.query.get_or_404(report_id)
        old_status = rpt.status
        rpt.status = new_status
        if data.get('reject_reason'):
            rpt.reject_reason = data.get('reject_reason')

        # 크래커 포인트 처리
        if rpt.user_id:
            member = Member.query.get(rpt.user_id)
            if member:
                if new_status == '처리 완료' and old_status != '처리 완료':
                    member.points += 20
                    db.session.add(PointLog(user_id=rpt.user_id, amount=20, reason='신고 처리 완료 보상'))
                elif new_status == '반려' and old_status != '반려':
                    member.points = max(0, member.points - 10)
                    db.session.add(PointLog(user_id=rpt.user_id, amount=-10, reason='신고 반려 (포인트 차감)'))

        db.session.commit()
        return jsonify({'success': True, 'message': f'상태가 {new_status}(으)로 변경되었습니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@alert_bp.route('/alert/view/<int:report_id>')
def alert_view(report_id):
    rpt = Report.query.get_or_404(report_id)
    ai_res = AiResult.query.filter_by(report_id=rpt.id).first()
    
    reporter = Member.query.get(rpt.user_id)
    reporter_name = reporter.nickname if reporter and reporter.nickname else (reporter.username if reporter else '알 수 없음')
    
    detail = {
        'id': rpt.id,
        'title': rpt.title or '도로 파손 신고',
        'content': rpt.content,
        'status': rpt.status,
        'time': rpt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'address': rpt.address,
        'lat': rpt.latitude,
        'lng': rpt.longitude,
        'file_path': rpt.file_path,
        'file_type': rpt.file_type,
        'reporter_name': reporter_name,
        'confidence': ai_res.confidence if ai_res else 0,
        'damage_type': ai_res.damage_type if ai_res else 'N/A'
    }
    
    return render_template('alert_view.html', detail=detail, is_admin=session.get('is_admin', False))

@alert_bp.route('/api/admin/notice', methods=['POST'])
def add_notice():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
    
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category = data.get('category', '일반')
    
    if not title or not content:
        return jsonify({'success': False, 'message': '제목과 내용을 입력해주세요.'}), 400
        
    try:
        new_notice = Notice(
            title=title,
            content=content,
            category=category,
            author_id=session.get('user_id')
        )
        db.session.add(new_notice)
        db.session.commit()
        return jsonify({'success': True, 'message': '공지사항이 등록되었습니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
