import math
from datetime import datetime, timedelta

from services.region_service import normalize_region_name
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from sqlalchemy import text

from database import db

alert_bp = Blueprint('alert', __name__)

VISIBLE_USER_STATUSES = {'접수완료', '처리중', '처리완료'}
ADMIN_ALERT_STATUSES = {'관리자 확인중', '접수완료', '처리중', '처리완료', '반려'}


def _safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(value)
    except Exception:
        return default


def _parse_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                pass
    return None


def haversine_m(lat1, lon1, lat2, lon2):
    lat1 = _safe_float(lat1)
    lon1 = _safe_float(lon1)
    lat2 = _safe_float(lat2)
    lon2 = _safe_float(lon2)
    if not (lat1 or lon1 or lat2 or lon2):
        return 999999.0
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _current_user_role():
    role = session.get('user_role') or session.get('role')
    if role:
        return role

    user_id = session.get('user_id')
    if not user_id:
        return 'user'

    sql = text("""
        SELECT
            COALESCE(role, CASE WHEN is_admin = 1 THEN 'admin' ELSE 'user' END) AS role_value,
            is_admin,
            nickname,
            username
        FROM members
        WHERE id = :user_id
        LIMIT 1
    """)
    row = db.session.execute(sql, {'user_id': user_id}).mappings().first()
    if not row:
        return 'user'

    role_value = row.get('role_value') or ('admin' if _safe_int(row.get('is_admin')) == 1 else 'user')
    session['user_role'] = role_value
    session['role'] = role_value
    session['is_admin'] = role_value == 'admin' or _safe_int(row.get('is_admin')) == 1
    session['user_name'] = row.get('nickname') or row.get('username') or '사용자'
    return role_value

def _get_manager_region():
    region = session.get('manager_region')
    if region:
        return region

    user_id = session.get('user_id')
    if not user_id:
        return None

    sql = text("""
        SELECT manager_region
        FROM members
        WHERE id = :user_id
        LIMIT 1
    """)

    row = db.session.execute(sql, {'user_id': user_id}).mappings().first()

    region = row.get('manager_region') if row else None
    session['manager_region'] = region

    return region


def _latest_ai_join_sql():
    return """
        LEFT JOIN (
            SELECT a1.*
            FROM ai_results a1
            INNER JOIN (
                SELECT report_id, MAX(id) AS max_id
                FROM ai_results
                GROUP BY report_id
            ) a2 ON a1.id = a2.max_id
        ) ai ON ai.report_id = r.id
    """


def _fetch_reports():
    sql = text(f"""
        SELECT
            r.id,
            r.title,
            r.content,
            r.latitude,
            r.longitude,
            r.file_path,
            r.file_type,
            r.created_at,
            r.user_id,
            r.status,
            r.reject_reason,
            r.region_name,
            r.last_checked_at,
            r.thumbnail_path,
            ai.is_damaged,
            ai.confidence,
            ai.damage_type,
            m.username,
            m.nickname,
            m.manager_region,
            COALESCE(m.role, CASE WHEN m.is_admin = 1 THEN 'admin' ELSE 'user' END) AS member_role,
            m.is_admin,
            m.active
        FROM report r
        {_latest_ai_join_sql()}
        LEFT JOIN members m ON m.id = r.user_id
        ORDER BY r.created_at DESC, r.id DESC
    """)
    return [dict(row) for row in db.session.execute(sql).mappings().all()]


def _build_groups(items):
    normalized = []
    for raw in items:
        item = dict(raw)
        item['created_at'] = _parse_dt(item.get('created_at'))
        item['risk_score'] = _safe_float(item.get('confidence'))
        item['image_path'] = item.get('thumbnail_path') or item.get('file_path') or ''
        item['region_name'] = normalize_region_name(item.get('region_name') or item.get('content'))
        item['location'] = item.get('region_name') or item.get('content') or '위치 정보 없음'
        normalized.append(item)

    groups = []
    visited = set()
    for item in normalized:
        item_id = item['id']
        if item_id in visited:
            continue
        queue = [item]
        component = []
        visited.add(item_id)
        while queue:
            current = queue.pop()
            component.append(current)
            current_dt = current.get('created_at')
            for other in normalized:
                other_id = other['id']
                if other_id in visited:
                    continue
                other_dt = other.get('created_at')
                if current_dt is None or other_dt is None:
                    continue
                if abs((current_dt - other_dt).total_seconds()) > 86400:
                    continue
                if haversine_m(current.get('latitude'), current.get('longitude'), other.get('latitude'), other.get('longitude')) > 50:
                    continue
                visited.add(other_id)
                queue.append(other)
        groups.append(component)

    group_map = {}
    for group in groups:
        distinct_users = len({g.get('user_id') for g in group if g.get('user_id') is not None})
        representative = max(
            group,
            key=lambda x: (_safe_float(x.get('risk_score')), x.get('created_at') or datetime.min, x.get('id') or 0)
        )
        for member in group:
            urgent_reasons = []
            if _safe_float(representative.get('risk_score')) >= 80:
                urgent_reasons.append('고위험')
            if distinct_users >= 3:
                urgent_reasons.append('반복 제보')
            created_at = member.get('created_at')
            status = member.get('status') or ''
            if created_at and status in ('접수완료', '관리자 확인중') and (datetime.now() - created_at).total_seconds() >= 86400:
                urgent_reasons.append('장기 미처리')
            member['group_reporter_count'] = distinct_users or 1
            member['urgent_reason'] = ', '.join(urgent_reasons)
            group_map[member['id']] = {
                'group_ids': [g['id'] for g in group],
                'representative_id': representative.get('id'),
                'group_reporter_count': distinct_users or 1,
                'urgent_reason': member['urgent_reason'],
            }
    return normalized, group_map


def _selected_point():
    lat = request.args.get('lat') or session.get('selected_lat')
    lng = request.args.get('lng') or session.get('selected_lng')
    return _safe_float(lat, None), _safe_float(lng, None)


def _status_class(status):
    if status == '접수완료':
        return 'status-received'
    if status == '처리중':
        return 'status-processing'
    if status == '처리완료':
        return 'status-done'
    if status == '반려':
        return 'status-rejected'
    if status == '관리자 확인중':
        return 'status-review'
    return 'status-default'


def _risk_payload(score):
    score = _safe_float(score)
    if score >= 80:
        return 'high', 'risk-high'
    if score >= 50:
        return 'medium', 'risk-medium'
    return 'low', 'risk-low'


def _priority_score(item):
    score = 0
    status = item.get('status') or ''
    risk_score = _safe_float(item.get('risk_score'))
    reporters = _safe_int(item.get('group_reporter_count'), 1)
    created_at = item.get('created_at')
    if status in ('접수완료', '관리자 확인중'):
        score += 100
    if risk_score >= 80:
        score += 50
    elif risk_score >= 50:
        score += 20
    if reporters >= 5:
        score += 40
    elif reporters >= 3:
        score += 30
    elif reporters >= 2:
        score += 10
    if created_at and status in ('접수완료', '관리자 확인중') and (datetime.now() - created_at).total_seconds() >= 86400:
        score += 40
    return score


def _serialize_alert_item(item, selected_lat=None, selected_lng=None):
    risk_text, risk_class = _risk_payload(item.get('risk_score'))
    distance_m = 0
    if selected_lat is not None and selected_lng is not None:
        distance_m = int(round(haversine_m(selected_lat, selected_lng, item.get('latitude'), item.get('longitude'))))
    return {
        'id': item.get('id'),
        'title': item.get('title') or '제목 없음',
        'content': item.get('content') or '',
        'location': item.get('location') or '위치 정보 없음',
        'distance_m': distance_m,
        'risk_text': risk_text,
        'risk_class': risk_class,
        'risk_score': int(round(_safe_float(item.get('risk_score')))),
        'status': item.get('status') or '-',
        'status_class': _status_class(item.get('status') or ''),
        'group_reporter_count': _safe_int(item.get('group_reporter_count'), 1),
        'created_at': item.get('created_at').strftime('%m-%d %H:%M') if item.get('created_at') else '-',
        'image_path': item.get('image_path') or '',
        'latitude': item.get('latitude'),
        'longitude': item.get('longitude'),
        'reject_reason': item.get('reject_reason') or '',
        'username': item.get('username') or '',
        'nickname': item.get('nickname') or '',
        'urgent_reason': item.get('urgent_reason') or '',
        'priority_score': _priority_score(item),
    }


def _load_alert_items():
    raw = _fetch_reports()
    normalized, group_map = _build_groups(raw)
    for item in normalized:
        meta = group_map.get(item['id'], {})
        item['group_reporter_count'] = meta.get('group_reporter_count', 1)
        item['urgent_reason'] = meta.get('urgent_reason', '')
        item['group_ids'] = meta.get('group_ids', [item['id']])
    return normalized

def _split_region_levels(region_text):
    if not region_text:
        return None, None, None

    parts = region_text.split()

    level1 = parts[0] if len(parts) > 0 else None  # 경기도
    level2 = parts[1] if len(parts) > 1 else None  # 수원시
    level3 = parts[2] if len(parts) > 2 else None  # 영통구

    return level1, level2, level3

@alert_bp.route('/alert')
def alert_page():
    # if not session.get('user_id'):
    #     return redirect(url_for('auth.login'))

    role = _current_user_role()
    items = _load_alert_items()
    selected_lat, selected_lng = _selected_point()

    # =========================
    # 🔥 관리자 / 매니저
    # =========================
    if role in ('admin', 'manager'):
        region_filter_on = request.args.get('region_filter', 'on') == 'on'

        # 🔹 관리자
        if role == 'admin':
            filtered = [
                item for item in items
                if (item.get('status') or '') in ADMIN_ALERT_STATUSES
            ]

            filtered.sort(
                key=lambda x: (
                    _priority_score(x),
                    _safe_float(x.get('risk_score')),
                    x.get('created_at') or datetime.min
                ),
                reverse=True
            )

        # 🔹 매니저
        else:
            manager_region = _get_manager_region()
            manager_region = normalize_region_name(manager_region) or manager_region

            if not manager_region:
                filtered = [
                    item for item in items
                    if (item.get('status') or '') in ADMIN_ALERT_STATUSES
                ]
                filtered.sort(
                    key=lambda x: (
                        _priority_score(x),
                        _safe_float(x.get('risk_score')),
                        x.get('created_at') or datetime.min
                    ),
                    reverse=True
                )
            else:
                m_lv1, m_lv2, m_lv3 = _split_region_levels(manager_region)

                priority_list = []
                secondary_list = []
                others = []

                for item in items:
                    status = item.get('status') or ''
                    if status not in ADMIN_ALERT_STATUSES:
                        continue

                    raw_region = item.get('region_name') or ''
                    normalized_region = normalize_region_name(raw_region) or raw_region
                    r_lv1, r_lv2, r_lv3 = _split_region_levels(normalized_region)

                    if m_lv1 == r_lv1 and m_lv2 == r_lv2 and m_lv3 == r_lv3:
                        priority_list.append(item)
                    elif m_lv1 == r_lv1 and m_lv2 == r_lv2:
                        secondary_list.append(item)
                    else:
                        others.append(item)

                def sort_func(x):
                    return (
                        _priority_score(x),
                        _safe_float(x.get('risk_score')),
                        x.get('created_at') or datetime.min
                    )

                priority_list.sort(key=sort_func, reverse=True)
                secondary_list.sort(key=sort_func, reverse=True)
                others.sort(key=sort_func, reverse=True)

                if region_filter_on:
                    filtered = priority_list + secondary_list
                else:
                    filtered = priority_list + secondary_list + others

        alerts = [_serialize_alert_item(item, selected_lat, selected_lng) for item in filtered]

        return render_template(
            'admin_alert.html',
            alerts=alerts,
            KAKAO_JS_KEY=current_app.config.get('KAKAO_JS_KEY', ''),
            region_filter_on=region_filter_on,
            current_role=role
        )

    # =========================
    # 🔥 일반 사용자
    # =========================
    filtered = []
    for item in items:
        status = item.get('status') or ''
        risk_score = _safe_float(item.get('risk_score'))
        reporters = _safe_int(item.get('group_reporter_count'), 1)

        if status not in VISIBLE_USER_STATUSES:
            continue

        if risk_score >= 80 or reporters >= 3:
            filtered.append(item)

    filtered.sort(
        key=lambda x: (
            _safe_float(x.get('risk_score')),
            _safe_int(x.get('group_reporter_count'), 1),
            x.get('created_at') or datetime.min
        ),
        reverse=True
    )

    alerts = [_serialize_alert_item(item, selected_lat, selected_lng) for item in filtered]

    return render_template(
        'alert.html',
        alerts=alerts,
        KAKAO_JS_KEY=current_app.config.get('KAKAO_JS_KEY', '')
    )


@alert_bp.route('/alert/detail/<int:report_id>')
def alert_detail(report_id):
    if not session.get('user_id'):
        return jsonify({'ok': False, 'message': '로그인이 필요합니다.'}), 401

    items = _load_alert_items()
    selected_lat, selected_lng = _selected_point()
    target = next((item for item in items if _safe_int(item.get('id')) == report_id), None)
    if not target:
        return jsonify({'ok': False, 'message': '대상을 찾을 수 없습니다.'}), 404

    return jsonify({'ok': True, 'item': _serialize_alert_item(target, selected_lat, selected_lng)})
