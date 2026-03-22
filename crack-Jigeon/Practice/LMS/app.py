# pip install flask

# 플라스크란?
# 파이썬으로 만든 db연동 콘솔 프로그램을 웹으로 연결하는 프레임워크
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 것
# app.py 는 플라스크로 서버를 동작하기 위한 파일명 (기본파일)
# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
# static : 정적 파일을 모아놓는 곳 (html, css, js)
# templates : 동적 파일을 모아놓는 곳 (crud 화면, 레이아웃, index 등..)

import math
import os
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_from_directory
)

from common.Session import Session
from domain import *


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-me')

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_JS_KEY = os.getenv("KAKAO_JS_KEY")
DEFAULT_RADIUS_M = 500

# 주소 검색 시 도시 입력만으로도 해당 행정구 목록을 제공하기 위한 지역 데이터 사전
CITY_DISTRICT_MAP = {
    "수원시": ["장안구", "권선구", "팔달구", "영통구"],
    "성남시": ["수정구", "중원구", "분당구"],
    "안양시": ["만안구", "동안구"],
    "용인시": ["처인구", "기흥구", "수지구"],
    "고양시": ["덕양구", "일산동구", "일산서구"],
    "서울시": [
        "종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구",
        "성북구", "강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구",
        "양천구", "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구",
        "서초구", "강남구", "송파구", "강동구"
    ]
}


def normalize_region_name(region_text):
    if not region_text:
        return ''

    text = region_text.strip()
    parts = text.split()

    if len(parts) >= 2:
        first = parts[0]
        second = parts[1]

        if first.endswith('시') and (
            second.endswith('구') or second.endswith('군') or second.endswith('시')
        ):
            return f"{first} {second}"

    if len(parts) >= 1:
        return parts[0]

    return ''

def normalize_top_region_name(region_name):
    if not region_name:
        return '기타'

    text = str(region_name).strip()

    alias_map = {
        '서울': '서울특별시',
        '서울시': '서울특별시',
        '부산': '부산광역시',
        '부산시': '부산광역시',
        '대구': '대구광역시',
        '대구시': '대구광역시',
        '인천': '인천광역시',
        '인천시': '인천광역시',
        '광주': '광주광역시',
        '광주시': '광주광역시',
        '대전': '대전광역시',
        '대전시': '대전광역시',
        '울산': '울산광역시',
        '울산시': '울산광역시',
        '세종': '세종특별자치시',
        '세종시': '세종특별자치시',
        '경기': '경기도',
        '강원': '강원특별자치도',
        '충북': '충청북도',
        '충남': '충청남도',
        '전북': '전북특별자치도',
        '전남': '전라남도',
        '경북': '경상북도',
        '경남': '경상남도',
        '제주': '제주특별자치도',
        '제주도': '제주특별자치도',
        '경상도': '경상도',
        '전라도': '전라도',
        '충청도': '충청도'
    }

    return alias_map.get(text, text)

def extract_region_name_from_location(location):
    return normalize_region_name(location)

def split_region_hierarchy(region_text):
    if not region_text:
        return ('기타', None)

    text = str(region_text).strip()
    parts = text.split()

    if not parts:
        return ('기타', None)

    first = normalize_top_region_name(parts[0])
    second = parts[1] if len(parts) >= 2 else None

    metro_keywords = ('특별시', '광역시', '특별자치시', '특별자치도', '도')

    if first == '경상도':
        return ('경상권', second)

    if first == '전라도':
        return ('전라권', second)

    if first == '충청도':
        return ('충청권', second)

    if first.endswith(metro_keywords):
        top_region = first
        sub_region = second
        return (top_region, sub_region)

    if first.endswith('시'):
        gyeonggi_cities = {
            '수원시', '성남시', '안양시', '용인시', '고양시', '부천시', '화성시',
            '남양주시', '평택시', '의정부시', '시흥시', '파주시', '김포시',
            '광명시', '군포시', '광주시', '이천시', '오산시', '안산시'
        }

        if first in gyeonggi_cities:
            return ('경기도', first)

        return (first, second)

    return (first, second)

def parse_location_hierarchy(location):
    if not location:
        return {
            'level1': '기타',
            'level2': None,
            'level3': None
        }

    parts = str(location).strip().split()
    if not parts:
        return {
            'level1': '기타',
            'level2': None,
            'level3': None
        }

    level1 = None
    level2 = None
    level3 = None

    # 1단계: 광역/도 단위 판별
    first = parts[0]

    if (
        first.endswith('도')
        or first.endswith('특별시')
        or first.endswith('광역시')
        or first.endswith('특별자치시')
        or first.endswith('특별자치도')
        or first.endswith('자치시')
    ):
        level1 = first

        if len(parts) >= 2:
            level2 = parts[1]

        if len(parts) >= 3:
            # level2가 시/군이고, level3가 구일 수 있음
            if parts[1].endswith('시') or parts[1].endswith('군'):
                if parts[2].endswith('구'):
                    level3 = parts[2]
            # 특별시/광역시 안에서는 level2가 바로 구
            elif parts[1].endswith('구'):
                level3 = None

    else:
        # 2단계: 광역단위 없이 바로 시/군/구로 시작하는 경우
        if first.endswith('시') or first.endswith('군'):
            level1 = first

            if len(parts) >= 2:
                level2 = parts[1]

                if len(parts) >= 3 and parts[1].endswith('구'):
                    level3 = None

        elif first.endswith('구'):
            level1 = first

        else:
            level1 = first

    return {
        'level1': level1 or '기타',
        'level2': level2,
        'level3': level3
    }

def parse_region_hierarchy(region_name, location):
    location_text = (location or '').strip()
    location_parts = location_text.split()

    normalized_region = normalize_region_name(region_name)
    region_parts = normalized_region.split() if normalized_region else []

    level1 = None   # 도 / 광역시 / 특별시
    level2 = None   # 시 / 군 / 구
    level3 = None   # 구 (경기도 수원시 영통구 같은 케이스에서만 사용)

    metro_suffixes = ('특별시', '광역시', '특별자치시', '특별자치도', '도')

    # 1. region_name 기준 우선 파싱
    if len(region_parts) >= 2:
        first = region_parts[0]
        second = region_parts[1]

        if first.endswith(metro_suffixes):
            level1 = first
            level2 = second
        elif first.endswith('시') or first.endswith('군'):
            # 예: 수원시 영통구 -> 경기도 / 수원시 / 영통구 로 보정해야 함
            gyeonggi_cities = {
                '수원시', '성남시', '안양시', '용인시', '고양시', '부천시', '화성시',
                '남양주시', '평택시', '의정부시', '시흥시', '파주시', '김포시',
                '광명시', '군포시', '광주시', '이천시', '오산시', '안산시'
            }

            if first in gyeonggi_cities:
                level1 = '경기도'
                level2 = first
                if second.endswith('구'):
                    level3 = second
            else:
                level1 = first
                level2 = second

    elif len(region_parts) == 1:
        first = region_parts[0]

        if first.endswith(metro_suffixes):
            level1 = first
        elif first.endswith('시') or first.endswith('군'):
            gyeonggi_cities = {
                '수원시', '성남시', '안양시', '용인시', '고양시', '부천시', '화성시',
                '남양주시', '평택시', '의정부시', '시흥시', '파주시', '김포시',
                '광명시', '군포시', '광주시', '이천시', '오산시', '안산시'
            }

            if first in gyeonggi_cities:
                level1 = '경기도'
                level2 = first
            else:
                level1 = first

    # 2. location으로 부족한 단계 보완
    if not level1:
        if location_parts:
            first = location_parts[0]

            if first.endswith(metro_suffixes):
                level1 = first
                if len(location_parts) >= 2:
                    level2 = location_parts[1]
                if len(location_parts) >= 3 and location_parts[2].endswith('구'):
                    level3 = location_parts[2]

            elif first.endswith('시') or first.endswith('군'):
                gyeonggi_cities = {
                    '수원시', '성남시', '안양시', '용인시', '고양시', '부천시', '화성시',
                    '남양주시', '평택시', '의정부시', '시흥시', '파주시', '김포시',
                    '광명시', '군포시', '광주시', '이천시', '오산시', '안산시'
                }

                if first in gyeonggi_cities:
                    level1 = '경기도'
                    level2 = first
                    if len(location_parts) >= 2 and location_parts[1].endswith('구'):
                        level3 = location_parts[1]
                else:
                    level1 = first
                    if len(location_parts) >= 2:
                        level2 = location_parts[1]

            else:
                level1 = first

    else:
        # 이미 level1, level2가 잡혔으면 location으로 level3만 보정
        if level1 == '경기도':
            if len(location_parts) >= 3 and location_parts[2].endswith('구'):
                level3 = location_parts[2]
            elif len(location_parts) >= 2 and location_parts[1].endswith('구'):
                level3 = location_parts[1]

        elif level1.endswith(('특별시', '광역시', '특별자치시')):
            # 서울특별시 강남구 역삼동 -> 여기서는 강남구까지만
            if not level2 and len(location_parts) >= 2 and location_parts[1].endswith('구'):
                level2 = location_parts[1]

    return {
        'level1': level1 or '기타',
        'level2': level2,
        'level3': level3
    }

# 두 좌표 사이 실제 거리를 계산하여 위치 기반 사건 필터링에 사용하는 함수
def haversine_m(lat1, lon1, lat2, lon2):
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    r = 6371000  # meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return r * c


def is_visible_to_user(incident):
    risk_score = float(incident.get('risk_score') or 0)
    reporter_count = int(incident.get('group_reporter_count') or 0)

    return (
        risk_score >= 80 or
        reporter_count >= 3
    )


def serialize_incident(i):
    return {
        'id': i.get('id'),
        'title': i.get('title'),
        'location': i.get('location'),
        'region_name': normalize_region_name(i.get('region_name')),
        'status': i.get('status'),
        'reject_reason': i.get('reject_reason'),
        'risk_score': float(i.get('risk_score') or 0),
        'first_created_at': i.get('first_created_at').strftime('%m-%d %H:%M') if i.get('first_created_at') else '',
        'latitude': i.get('latitude'),
        'longitude': i.get('longitude'),
        'distance_m': i.get('distance_m'),
        'group_reporter_count': int(i.get('group_reporter_count') or 0),
        'image_path': i.get('image_path')
    }


def group_incidents(raw_incidents):
    grouped_incidents = []
    used_ids = set()

    for incident in raw_incidents:
        if incident['id'] in used_ids:
            continue

        base_lat = incident.get('latitude')
        base_lng = incident.get('longitude')
        base_time = incident.get('first_created_at')

        reporter_ids = set()
        if incident.get('member_id'):
            reporter_ids.add(incident.get('member_id'))

        group_members = [incident]
        used_ids.add(incident['id'])

        for other in raw_incidents:
            if other['id'] == incident['id']:
                continue
            if other['id'] in used_ids:
                continue

            other_time = other.get('first_created_at')
            other_lat = other.get('latitude')
            other_lng = other.get('longitude')

            if base_lat is None or base_lng is None or other_lat is None or other_lng is None:
                continue

            distance_m = haversine_m(base_lat, base_lng, other_lat, other_lng)
            time_diff_sec = abs((base_time - other_time).total_seconds()) if base_time and other_time else 999999

            if distance_m <= 50 and time_diff_sec <= 86400:
                used_ids.add(other['id'])
                group_members.append(other)

                if other.get('member_id'):
                    reporter_ids.add(other.get('member_id'))

        representative = max(
            group_members,
            key=lambda x: (
                float(x.get('risk_score') or 0),
                x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
            )
        )

        representative['group_reporter_count'] = len(reporter_ids)
        grouped_incidents.append(representative)

    return grouped_incidents


def build_urgent_reasons(incident, now=None):
    if now is None:
        now = datetime.now()

    reasons = []
    risk_score = float(incident.get('risk_score') or 0)
    reporter_count = int(incident.get('group_reporter_count') or 0)
    status = incident.get('status')
    created_at = incident.get('first_created_at')

    if risk_score >= 80:
        reasons.append('고위험')

    if reporter_count >= 3:
        reasons.append('반복 제보')

    if status == '접수완료' and created_at and (now - created_at).total_seconds() >= 86400:
        reasons.append('장기 미처리')

    return reasons


def get_priority_score(incident, now=None):
    if now is None:
        now = datetime.now()

    score = 0
    risk_score = float(incident.get('risk_score') or 0)
    reporter_count = int(incident.get('group_reporter_count') or 0)
    status = incident.get('status')
    created_at = incident.get('first_created_at')

    if status == '접수완료':
        score += 100

    if risk_score >= 80:
        score += 50
    elif risk_score >= 50:
        score += 20

    if reporter_count >= 5:
        score += 40
    elif reporter_count >= 3:
        score += 30
    elif reporter_count >= 2:
        score += 10

    if status == '접수완료' and created_at and (now - created_at).total_seconds() >= 86400:
        score += 40

    return score


def get_priority_label(priority_score):
    if priority_score >= 150:
        return '긴급'
    elif priority_score >= 80:
        return '주의'
    return '일반'


def find_group_incident_ids(target_incident, raw_incidents):
    group_ids = []

    base_lat = target_incident.get('latitude')
    base_lng = target_incident.get('longitude')
    base_time = target_incident.get('first_created_at')

    if base_lat is None or base_lng is None or base_time is None:
        return [target_incident.get('id')]

    for incident in raw_incidents:
        other_id = incident.get('id')
        other_lat = incident.get('latitude')
        other_lng = incident.get('longitude')
        other_time = incident.get('first_created_at')

        if other_lat is None or other_lng is None or other_time is None:
            continue

        distance_m = haversine_m(base_lat, base_lng, other_lat, other_lng)
        time_diff_sec = abs((base_time - other_time).total_seconds())

        if distance_m <= 50 and time_diff_sec <= 86400:
            group_ids.append(other_id)

    if not group_ids:
        return [target_incident.get('id')]

    return group_ids

def build_incident_groups(raw_incidents):
    groups = []
    used_ids = set()

    for incident in raw_incidents:
        if incident['id'] in used_ids:
            continue

        base_lat = incident.get('latitude')
        base_lng = incident.get('longitude')
        base_time = incident.get('first_created_at')

        group_members = [incident]
        used_ids.add(incident['id'])

        for other in raw_incidents:
            if other['id'] == incident['id']:
                continue
            if other['id'] in used_ids:
                continue

            other_time = other.get('first_created_at')
            other_lat = other.get('latitude')
            other_lng = other.get('longitude')

            if base_lat is None or base_lng is None or other_lat is None or other_lng is None:
                continue

            distance_m = haversine_m(base_lat, base_lng, other_lat, other_lng)
            time_diff_sec = abs((base_time - other_time).total_seconds()) if base_time and other_time else 999999

            if distance_m <= 50 and time_diff_sec <= 86400:
                used_ids.add(other['id'])
                group_members.append(other)

        representative = max(
            group_members,
            key=lambda x: (
                float(x.get('risk_score') or 0),
                x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
            )
        )

        groups.append({
            'representative': representative,
            'members': group_members
        })

    return groups


def sync_duplicate_group_statuses(cursor):
    cursor.execute("""
        SELECT
            id,
            latitude,
            longitude,
            first_created_at,
            risk_score,
            status,
            reject_reason
        FROM incidents
        ORDER BY first_created_at DESC
    """)
    raw_incidents = cursor.fetchall()

    groups = build_incident_groups(raw_incidents)
    synced_group_count = 0

    for group in groups:
        members = group['members']
        representative = group['representative']

        if len(members) < 2:
            continue

        target_status = representative.get('status') or '접수완료'

        if target_status == '반려':
            target_reject_reason = representative.get('reject_reason') or ''
            if not target_reject_reason:
                for member in members:
                    if member.get('reject_reason'):
                        target_reject_reason = member.get('reject_reason')
                        break
        else:
            target_reject_reason = None

        need_sync = False
        for member in members:
            member_status = member.get('status')
            member_reject_reason = member.get('reject_reason') or ''

            if member_status != target_status:
                need_sync = True
                break

            if target_status == '반려':
                if member_reject_reason != (target_reject_reason or ''):
                    need_sync = True
                    break
            else:
                if member.get('reject_reason') is not None:
                    need_sync = True
                    break

        if not need_sync:
            continue

        group_ids = [member['id'] for member in members]
        placeholders = ', '.join(['%s'] * len(group_ids))

        if target_status == '반려':
            sql = f"""
                UPDATE incidents
                SET status = %s, reject_reason = %s
                WHERE id IN ({placeholders})
            """
            params = [target_status, target_reject_reason] + group_ids
        else:
            sql = f"""
                UPDATE incidents
                SET status = %s, reject_reason = NULL
                WHERE id IN ({placeholders})
            """
            params = [target_status] + group_ids

        cursor.execute(sql, params)
        synced_group_count += 1

    return synced_group_count


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    selected_tab = request.args.get('tab', 'urgent').strip()

    allowed_tabs = ['urgent', 'today', 'pending', 'long_pending', 'rejected']
    if selected_tab not in allowed_tabs:
        selected_tab = 'urgent'

    conn = Session.get_connection()

    try:
        with conn.cursor() as cursor:
            sync_duplicate_group_statuses(cursor)
            conn.commit()

            sql = """
                SELECT
                    i.id,
                    i.member_id,
                    i.title,
                    i.location,
                    i.region_name,
                    i.latitude,
                    i.longitude,
                    i.image_path,
                    i.status,
                    i.risk_score,
                    i.first_created_at,
                    i.last_checked_at
                FROM incidents i
                ORDER BY i.first_created_at DESC
            """
            cursor.execute(sql)
            raw_incidents = cursor.fetchall()

            grouped_incidents = group_incidents(raw_incidents)

            region_stats = {}
            for incident in grouped_incidents:
                region = normalize_region_name(incident.get('region_name')) or '기타'

                if region not in region_stats:
                    region_stats[region] = {
                        'total': 0,
                        'pending': 0,
                        'processing': 0,
                        'rejected': 0
                    }

                region_stats[region]['total'] += 1

                status = incident.get('status')
                if status == '접수완료':
                    region_stats[region]['pending'] += 1
                elif status == '처리중':
                    region_stats[region]['processing'] += 1
                elif status == '반려':
                    region_stats[region]['rejected'] += 1

            region_stats_list = sorted(
                [{'region': k, **v} for k, v in region_stats.items()],
                key=lambda x: (x['pending'], x['processing'], x['total']),
                reverse=True
            )

            today = datetime.now().date()
            now = datetime.now()

            long_pending_count = sum(
                1 for i in grouped_incidents
                if i.get('status') == '접수완료'
                and i.get('first_created_at')
                and (now - i.get('first_created_at')).total_seconds() >= 86400
            )

            summary = {
                "urgent_count": sum(
                    1 for i in grouped_incidents
                    if i.get('status') in ['접수완료', '처리중']
                    and get_priority_label(get_priority_score(i, now)) == '긴급'
                ),
                "today_count": sum(
                    1 for i in grouped_incidents
                    if i.get('first_created_at')
                    and i.get('first_created_at').date() == today
                ),
                "pending_count": sum(
                    1 for i in grouped_incidents
                    if i.get('status') == '접수완료'
                ),
                "long_pending_count": long_pending_count,
                "rejected_count": sum(
                    1 for i in grouped_incidents
                    if i.get('status') == '반려'
                )
            }

            for incident in grouped_incidents:
                reasons = build_urgent_reasons(incident, now)
                incident['urgent_reason'] = ', '.join(reasons)

                priority_score = get_priority_score(incident, now)
                incident['priority_score'] = priority_score
                incident['priority_label'] = get_priority_label(priority_score)

            urgent_all = sorted(
                [
                    incident for incident in grouped_incidents
                    if incident.get('status') in ['접수완료', '처리중']
                    and incident.get('urgent_reason')
                ],
                key=lambda x: (
                    x.get('priority_score') or 0,
                    x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
                ),
                reverse=True
            )

            today_all = sorted(
                [
                    incident for incident in grouped_incidents
                    if incident.get('first_created_at')
                    and incident.get('first_created_at').date() == today
                ],
                key=lambda x: x.get('first_created_at').timestamp() if x.get('first_created_at') else 0,
                reverse=True
            )

            pending_all = sorted(
                [
                    incident for incident in grouped_incidents
                    if incident.get('status') == '접수완료'
                ],
                key=lambda x: x.get('first_created_at').timestamp() if x.get('first_created_at') else 0,
                reverse=True
            )

            long_pending_all = sorted(
                [
                    incident for incident in grouped_incidents
                    if incident.get('status') == '접수완료'
                    and incident.get('first_created_at')
                    and (now - incident.get('first_created_at')).total_seconds() >= 86400
                ],
                key=lambda x: x.get('first_created_at').timestamp() if x.get('first_created_at') else 0,
                reverse=True
            )

            rejected_all = sorted(
                [
                    incident for incident in grouped_incidents
                    if incident.get('status') == '반려'
                ],
                key=lambda x: x.get('first_created_at').timestamp() if x.get('first_created_at') else 0,
                reverse=True
            )

            dashboard_tab_map = {
                'urgent': {
                    'title': '긴급 조치 필요',
                    'subtitle': '고위험 또는 반복 제보로 우선 확인이 필요한 신고입니다.',
                    'items': urgent_all,
                    'more_url': '/admin/incidents?quick_filter=urgent'
                },
                'today': {
                    'title': '오늘 접수 신고',
                    'subtitle': '오늘 새로 등록된 신고 목록입니다.',
                    'items': today_all,
                    'more_url': '/admin/incidents?quick_filter=today'
                },
                'pending': {
                    'title': '미처리 신고',
                    'subtitle': '아직 검토 전인 신고 목록입니다.',
                    'items': pending_all,
                    'more_url': '/admin/incidents?quick_filter=pending'
                },
                'long_pending': {
                    'title': '장기 미처리 신고',
                    'subtitle': '24시간 이상 조치되지 않은 신고 목록입니다.',
                    'items': long_pending_all,
                    'more_url': '/admin/incidents?quick_filter=long_pending'
                },
                'rejected': {
                    'title': '반려 신고',
                    'subtitle': '관리 기준에 따라 반려된 신고 목록입니다.',
                    'items': rejected_all,
                    'more_url': '/admin/incidents?quick_filter=rejected'
                }
            }

            selected_tab_info = dashboard_tab_map[selected_tab]
            dashboard_items_all = selected_tab_info['items']
            dashboard_items = dashboard_items_all[:6]
            dashboard_has_more = len(dashboard_items_all) > 6
            dashboard_more_url = selected_tab_info['more_url']
            dashboard_section_title = selected_tab_info['title']
            dashboard_section_subtitle = selected_tab_info['subtitle']

            return render_template(
                'admin_dashboard.html',
                summary=summary,
                selected_tab=selected_tab,
                dashboard_items=dashboard_items,
                dashboard_has_more=dashboard_has_more,
                dashboard_more_url=dashboard_more_url,
                dashboard_section_title=dashboard_section_title,
                dashboard_section_subtitle=dashboard_section_subtitle
            )
    finally:
        conn.close()


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(current_dir, 'static', 'uploads')
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        return f"파일 없음: {file_path}", 404

    return send_from_directory(upload_folder, filename)


# 주소 검색 API
@app.route('/api/address/search')
def address_search():
    keyword = request.args.get('q', '').strip()

    if not keyword:
        return jsonify({
            'success': False,
            'message': '검색어를 입력해주세요.',
            'items': []
        }), 400

    # 도시 이름만 입력해도 전체 지역과 하위 행정구를 즉시 확장해 보여주는 검색 보완 로직
    matched_city = None
    for city_name in CITY_DISTRICT_MAP.keys():
        if keyword == city_name or keyword == city_name.replace('시', ''):
            matched_city = city_name
            break

    if matched_city:
        items = []

        # 시 전체 보기
        items.append({
            'address_name': f"{matched_city} 전체",
            'latitude': None,
            'longitude': None,
            'is_city_district': True,
            'city': matched_city,
            'district': ''
        })

        # 구 목록
        for district in CITY_DISTRICT_MAP[matched_city]:
            items.append({
                'address_name': f"{matched_city} {district}",
                'latitude': None,
                'longitude': None,
                'is_city_district': True,
                'city': matched_city,
                'district': district
            })

        return jsonify({
            'success': True,
            'items': items
        })

    # 상세 주소 검색은 카카오 API 사용
    try:
        headers = {
            "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
        }
        params = {
            "query": keyword,
            "size": 10
        }

        resp = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers=headers,
            params=params,
            timeout=5
        )
        resp.raise_for_status()

        data = resp.json()
        items = []

        for doc in data.get('documents', []):
            road_addr = doc.get('road_address') or {}
            addr = doc.get('address') or {}

            address_name = (
                road_addr.get('address_name')
                or addr.get('address_name')
                or doc.get('address_name')
            )

            items.append({
                'address_name': address_name,
                'latitude': float(doc.get('y')),
                'longitude': float(doc.get('x')),
                'is_city_district': False
            })

        return jsonify({
            'success': True,
            'items': items
        })

    except Exception as e:
        print(f"주소 검색 오류: {e}")
        return jsonify({
            'success': False,
            'message': '주소 검색 중 오류가 발생했습니다.',
            'items': []
        }), 500


# methods는 웹의 동작에 관여한다
# GET : URL 주소로 데이터를 처리 (보안상 좋지 않음, 대신 빠름)
# POST : BODY 영역의 데이터를 처리 (보안상 좋음, 대용량일 때 많이 사용됨)
# 대부분 처음에 화면(HTML 랜더)을 요청할 때는 GET 방식 처리
# 화면에 있는 내용을 백엔드로 전달할 때는 POST 방식 처리


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = 'SELECT id, name, uid, role FROM members WHERE uid = %s and password = %s'
            cursor.execute(sql, (uid, upw))
            user = cursor.fetchone()

            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_uid'] = user['uid']
                session['user_role'] = user['role']
                return redirect(url_for('index'))
            else:
                return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.');history.back();</script>"
    finally:
        conn.close()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')

    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디입니다.');history.back();</script>"

            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다.');location.href='/login';</script>"

    except Exception as e:
        print(f"회원가입 오류 : {e}")
        return "가입 중 오류가 발생했습니다. \n join()메서드를 확인하세요."
    finally:
        conn.close()


@app.route('/member/edit', methods=['GET', 'POST'])
def member_edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html', user=user_info)

            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw:
                sql = 'UPDATE members SET name = %s, password = %s WHERE id = %s'
                cursor.execute(sql, (new_name, new_pw, session['user_id']))
            else:
                sql = 'UPDATE members SET name = %s WHERE id = %s'
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_name'] = new_name

            return "<script>alert('정보가 수정되었습니다.');location.href='/mypage';</script>"

    except Exception as e:
        print(f"회원수정 오류 : {e}")
        return "수정 중 오류가 발생했습니다. \n member_edit()메서드를 확인하세요."
    finally:
        conn.close()


@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()

            cursor.execute(
                'SELECT COUNT(*) AS board_count FROM boards where member_id = %s',
                (session['user_id'],)
            )
            board_count = cursor.fetchone()['board_count']

            return render_template('mypage.html', user=user_info, board_count=board_count)
    finally:
        conn.close()


######################################## 회원 CRUD ########################################
####################################### 게시판 CRUD #######################################


@app.route('/board/write', methods=['GET', 'POST'])
def board_write():
    if request.method == 'GET':
        if 'user_id' not in session:
            return '<script>alert("로그인 후 이용 가능합니다.");location.href="/login";</script>'

        return render_template('board_write.html')

    elif request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        member_id = session.get('user_id')

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'INSERT INTO boards (member_id, title, content) VALUES (%s, %s, %s)'
                cursor.execute(sql, (member_id, title, content))
                conn.commit()

                return redirect(url_for('board_list'))

        except Exception as e:
            print(f"글쓰기 에러 : {e}")
            return "저장 중 에러가 발생했습니다."
        finally:
            conn.close()


@app.route('/board')
def board_list():
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT b.*, m.name as writer_name
                FROM boards b
                JOIN members m ON b.member_id = m.id
                ORDER BY b.id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            boards = [Board.from_db(row) for row in rows]
            return render_template('board_list.html', boards=boards)
    finally:
        conn.close()


@app.route('/board/view/<int:board_id>')
def board_view(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT b.*, m.name as writer_name, m.uid as writer_uid
                FROM boards b
                JOIN members m ON b.member_id = m.id
                WHERE b.id = %s
            """
            cursor.execute(sql, (board_id,))
            row = cursor.fetchone()

            print(row)

            if not row:
                return "<script>alert('존재하지 않는 게시글입니다.');history.back()</script>"

            board = Board.from_db(row)
            return render_template('board_view.html', board=board)
    finally:
        conn.close()


@app.route('/board/edit/<int:board_id>', methods=['GET', 'POST'])
def board_edit(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                sql = "SELECT * FROM boards WHERE id = %s"
                cursor.execute(sql, (board_id,))
                row = cursor.fetchone()

                if not row:
                    return "<script>alert('존재하지 않는 게시글입니다.');history.back()</script>"

                if row['member_id'] != session.get('user_id'):
                    return "<script>alert('수정 권한이 없습니다.');history.back()</script>"

                print(row)
                board = Board.from_db(row)
                return render_template('board_edit.html', board=board)

            elif request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')

                sql = "UPDATE boards SET title = %s, content = %s WHERE id = %s"
                cursor.execute(sql, (title, content, board_id))
                conn.commit()

                return redirect(url_for('board_view', board_id=board_id))
    finally:
        conn.close()


@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = 'DELETE FROM boards WHERE id = %s AND member_id = %s'
            cursor.execute(sql, (board_id, session['user_id']))
            conn.commit()

            if cursor.rowcount > 0:
                print(f"게시글 {board_id}번 삭제 성공")
                return redirect(url_for('board_list'))
            else:
                return "<script>alert('삭제할 수 없습니다.');history.back()</script>"

    except Exception as e:
        print(f"삭제 에러 : {e}")
        return "삭제 중 오류가 발생했습니다."
    finally:
        conn.close()


# 사용자가 선택한 위치 기준으로 주변 위험 사건을 조회하는 핵심 API
@app.route('/alerts')
def alert_page():
    search_lat = request.args.get('lat', type=float)
    search_lng = request.args.get('lng', type=float)
    search_address = request.args.get('address', '', type=str).strip()
    radius_m = request.args.get('radius_m', DEFAULT_RADIUS_M, type=int)
    search_city = request.args.get('city', '', type=str).strip()
    search_district = request.args.get('district', '', type=str).strip()
    selected_status = request.args.get('status', '', type=str).strip()

    if search_district and not search_city:
        search_district = ''

    if search_lat is None or search_lng is None:
        search_lat = None
        search_lng = None

    if radius_m is None or radius_m <= 0:
        radius_m = DEFAULT_RADIUS_M

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 4, type=int)

    if per_page <= 0 or per_page > 20:
        per_page = 4

    is_api = request.args.get('api', '0') == '1'
    user_role = session.get('user_role', 'user')
    user_id = session.get('user_id')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    i.id,
                    i.member_id,
                    i.title,
                    i.location,
                    i.region_name,
                    i.latitude,
                    i.longitude,
                    i.image_path,
                    i.status,
                    i.reject_reason,
                    i.risk_score,
                    i.first_created_at,
                    i.last_checked_at
                FROM incidents i
                ORDER BY i.first_created_at DESC
            """
            cursor.execute(sql)
            raw_incidents = cursor.fetchall()

            manager_region = None

            # manager인 경우 담당 지역 조회
            if user_role == 'manager':
                sql_manager = "SELECT manager_region FROM members WHERE id = %s"
                cursor.execute(sql_manager, (user_id,))
                manager_info = cursor.fetchone()

                if not manager_info or not manager_info.get('manager_region'):
                    return "<script>alert('담당 지역이 지정되지 않았습니다.');history.back();</script>"

                manager_region = normalize_region_name(manager_info.get('manager_region'))
                manager_full_region = manager_region
                manager_city = manager_full_region.split()[0] if manager_full_region else ''

                raw_incidents = [
                    incident for incident in raw_incidents
                    if (
                        normalize_region_name(incident.get('region_name')) == manager_full_region
                        or normalize_region_name(incident.get('region_name')).startswith(manager_city + ' ')
                    )
                ]

                raw_incidents.sort(
                    key=lambda incident: (
                        0 if normalize_region_name(incident.get('region_name')) == manager_full_region else 1,
                        -(incident.get('first_created_at').timestamp()) if incident.get('first_created_at') else 0
                    )
                )

            incidents = group_incidents(raw_incidents)

            region_options = sorted({
                (incident.get('region_name') or '').strip()
                for incident in incidents
                if (incident.get('region_name') or '').strip()
            })

            filtered_incidents = []

            for incident in incidents:
                incident_lat = incident.get('latitude')
                incident_lng = incident.get('longitude')

                # 일반 사용자만 필터 적용
                if user_role not in ['admin', 'manager'] and not is_visible_to_user(incident):
                    continue

                # 일반 사용자에게 반려 숨김
                if user_role not in ['admin', 'manager'] and incident.get('status') == '반려':
                    continue

                # 상태 필터
                if selected_status and incident.get('status') != selected_status:
                    continue

                if search_city:
                    normalized_region = normalize_region_name(incident.get('region_name'))

                    if search_district:
                        target_region = f"{search_city} {search_district}"
                        if normalized_region == target_region:
                            incident['distance_m'] = None
                            filtered_incidents.append(incident)
                    else:
                        if normalized_region.startswith(search_city):
                            incident['distance_m'] = None
                            filtered_incidents.append(incident)

                elif search_lat is not None and search_lng is not None:
                    if incident_lat is None or incident_lng is None:
                        continue

                    distance_m = haversine_m(search_lat, search_lng, incident_lat, incident_lng)

                    if distance_m <= radius_m:
                        incident['distance_m'] = round(distance_m)
                        filtered_incidents.append(incident)

                else:
                    incident['distance_m'] = None
                    filtered_incidents.append(incident)

            if search_lat is not None and search_lng is not None:
                filtered_incidents.sort(key=lambda x: x['distance_m'])

            if user_role == 'manager' and manager_region:
                manager_full_region = manager_region
                filtered_incidents.sort(
                    key=lambda incident: (
                        0 if normalize_region_name(incident.get('region_name')) == manager_full_region else 1,
                        -(incident.get('first_created_at').timestamp()) if incident.get('first_created_at') else 0
                    )
                )

            if user_role not in ['admin', 'manager']:
                filtered_incidents.sort(
                    key=lambda incident: (
                        -int(incident.get('group_reporter_count') or 0),
                        -(incident.get('first_created_at').timestamp()) if incident.get('first_created_at') else 0
                    )
                )

            total_count = len(filtered_incidents)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paged_incidents = filtered_incidents[start_idx:end_idx]
            has_next = end_idx < total_count

            print("검색 주소:", search_address)
            print("필터 전 개수:", len(incidents))
            print("필터 후 개수:", len(filtered_incidents))

            display_address = search_address
            filter_type = 'all'

            if search_city:
                filter_type = 'region'
                if search_district:
                    display_address = f"{search_city} {search_district}"
                else:
                    display_address = f"{search_city} 전체"
            elif search_lat is not None and search_lng is not None:
                filter_type = 'radius'

            # 권한별 화면 분리
            template_name = 'alert.html'
            if user_role in ['admin', 'manager']:
                template_name = 'admin_alert.html'

            if is_api:
                return jsonify({
                    'success': True,
                    'items': [serialize_incident(i) for i in paged_incidents],
                    'has_next': has_next,
                    'next_page': page + 1 if has_next else None
                })

            return render_template(
                template_name,
                incidents=paged_incidents,
                region_options=region_options,
                selected_status=selected_status,
                search_city=search_city,
                search_district=search_district,
                search_address=display_address,
                filter_type=filter_type,
                radius_m=radius_m,
                page=page,
                per_page=per_page,
                has_next=has_next,
                user_role=user_role
            )
    finally:
        conn.close()


@app.route('/admin/incidents')
def admin_incidents():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    quick_filter = request.args.get('quick_filter', '').strip()
    selected_status = request.args.get('status', '').strip()
    selected_risk = request.args.get('risk', '').strip()
    keyword = request.args.get('keyword', '').strip()
    sort_by = request.args.get('sort', '').strip()
    member_id = request.args.get('member_id', '').strip()

    sort_order = request.args.get('order', 'desc').strip().lower()
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    if not sort_by:
        if quick_filter == 'urgent':
            sort_by = 'priority'
        elif quick_filter == 'pending':
            sort_by = 'pending'
        elif quick_filter == 'long_pending':
            sort_by = 'pending'
        else:
            sort_by = 'latest'
    selected_region = request.args.get('region', '').strip()

    page = int(request.args.get('page', 1))
    per_page = 6

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sync_duplicate_group_statuses(cursor)
            conn.commit()

            sql = """
                SELECT
                    i.id,
                    i.title,
                    i.location,
                    i.status,
                    i.reject_reason,
                    i.risk_score,
                    i.first_created_at,
                    i.image_path,
                    i.latitude,
                    i.longitude,
                    i.member_id,
                    i.region_name
                FROM incidents i
                ORDER BY i.first_created_at DESC
            """
            cursor.execute(sql)
            raw_incidents = cursor.fetchall()

            if member_id:
                raw_incidents = [
                    incident for incident in raw_incidents
                    if str(incident.get('member_id') or '') == member_id
                ]

            incidents = group_incidents(raw_incidents)

            region_options = sorted({
                (incident.get('region_name') or '').strip()
                for incident in incidents
                if (incident.get('region_name') or '').strip()
            })

            filtered_incidents = []
            now = datetime.now()

            for incident in incidents:
                score = float(incident.get('risk_score') or 0)
                title = (incident.get('title') or '').lower()
                location = (incident.get('location') or '').lower()
                region_name = (incident.get('region_name') or '').strip()

                reasons = build_urgent_reasons(incident, now)
                incident['urgent_reason'] = ', '.join(reasons)

                priority_score = get_priority_score(incident, now)
                incident['priority_score'] = priority_score
                incident['priority_label'] = get_priority_label(priority_score)

                if quick_filter == 'urgent':
                    if not (
                        incident.get('status') in ['접수완료', '처리중']
                        and incident.get('urgent_reason')
                    ):
                        continue

                elif quick_filter == 'today':
                    if not (
                        incident.get('first_created_at')
                        and incident.get('first_created_at').date() == now.date()
                    ):
                        continue

                elif quick_filter == 'pending':
                    if incident.get('status') != '접수완료':
                        continue

                elif quick_filter == 'long_pending':
                    if not (
                        incident.get('status') == '접수완료'
                        and incident.get('first_created_at')
                        and (now - incident.get('first_created_at')).total_seconds() >= 86400
                    ):
                        continue

                elif quick_filter == 'rejected':
                    if incident.get('status') != '반려':
                        continue

                if selected_region and region_name != selected_region:
                    continue

                if selected_status and incident.get('status') != selected_status:
                    continue

                if selected_risk == 'high' and score < 80:
                    continue
                elif selected_risk == 'medium' and (score < 50 or score >= 80):
                    continue
                elif selected_risk == 'low' and score >= 50:
                    continue

                if keyword:
                    keyword_lower = keyword.lower()
                    if keyword_lower not in title and keyword_lower not in location:
                        continue

                filtered_incidents.append(incident)

            reverse_sort = (sort_order == 'desc')

            if sort_by == 'id':
                filtered_incidents.sort(
                    key=lambda x: int(x.get('id') or 0),
                    reverse=reverse_sort
                )

            elif sort_by == 'location':
                filtered_incidents.sort(
                    key=lambda x: (x.get('location') or ''),
                    reverse=reverse_sort
                )

            elif sort_by == 'priority':
                filtered_incidents.sort(
                    key=lambda x: (
                        get_priority_score(x),
                        x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
                    ),
                    reverse=reverse_sort
                )

            elif sort_by == 'risk':
                filtered_incidents.sort(
                    key=lambda x: (
                        float(x.get('risk_score') or 0),
                        x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
                    ),
                    reverse=reverse_sort
                )

            elif sort_by == 'reports':
                filtered_incidents.sort(
                    key=lambda x: (
                        int(x.get('group_reporter_count') or 0),
                        x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
                    ),
                    reverse=reverse_sort
                )

            elif sort_by == 'status':
                status_order_map = {
                    '접수완료': 0,
                    '처리중': 1,
                    '처리완료': 2,
                    '반려': 3
                }
                filtered_incidents.sort(
                    key=lambda x: (
                        status_order_map.get(x.get('status'), 99),
                        x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
                    ),
                    reverse=reverse_sort
                )

            elif sort_by == 'pending':
                filtered_incidents.sort(
                    key=lambda x: (
                        0 if x.get('status') == '접수완료' else 1,
                        x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
                    ),
                    reverse=reverse_sort
                )

            else:  # latest
                filtered_incidents.sort(
                    key=lambda x: x.get('first_created_at').timestamp() if x.get('first_created_at') else 0,
                    reverse=reverse_sort
                )

            total_count = len(filtered_incidents)
            total_pages = (total_count + per_page - 1) // per_page

            if page < 1:
                page = 1

            if total_pages > 0 and page > total_pages:
                page = total_pages

            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paged_incidents = filtered_incidents[start_idx:end_idx]

            return render_template(
                'admin_incidents.html',
                incidents=paged_incidents,
                selected_status=selected_status,
                selected_risk=selected_risk,
                keyword=keyword,
                sort_by=sort_by,
                selected_region=selected_region,
                region_options=region_options,
                page=page,
                total_pages=total_pages,
                quick_filter=quick_filter,
                current_query_string=request.query_string.decode('utf-8')
            )
    finally:
        conn.close()


@app.route('/admin/incidents/group/<int:incident_id>')
def admin_incident_group_detail(incident_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401

    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sync_duplicate_group_statuses(cursor)
            conn.commit()

            cursor.execute("""
                SELECT
                    i.id,
                    i.member_id,
                    m.name AS member_name,
                    i.title,
                    i.location,
                    i.region_name,
                    i.latitude,
                    i.longitude,
                    i.image_path,
                    i.status,
                    i.reject_reason,
                    i.risk_score,
                    i.first_created_at,
                    i.last_checked_at
                FROM incidents i
                LEFT JOIN members m
                  ON i.member_id = m.id
                ORDER BY i.first_created_at DESC
            """)
            raw_incidents = cursor.fetchall()

            target_incident = None
            for item in raw_incidents:
                if item.get('id') == incident_id:
                    target_incident = item
                    break

            if not target_incident:
                return jsonify({'success': False, 'message': '존재하지 않는 사건입니다.'}), 404

            group_ids = find_group_incident_ids(target_incident, raw_incidents)
            group_items = [item for item in raw_incidents if item.get('id') in group_ids]

            representative = max(
                group_items,
                key=lambda x: (
                    float(x.get('risk_score') or 0),
                    x.get('first_created_at').timestamp() if x.get('first_created_at') else 0
                )
            )

            items = []
            for item in sorted(
                group_items,
                key=lambda x: x.get('first_created_at').timestamp() if x.get('first_created_at') else 0,
                reverse=True
            ):
                items.append({
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'member_name': item.get('member_name') or f"회원#{item.get('member_id')}",
                    'location': item.get('location'),
                    'status': item.get('status'),
                    'first_created_at': item.get('first_created_at').strftime('%m-%d %H:%M') if item.get(
                        'first_created_at') else '-',
                    'is_representative': item.get('id') == representative.get('id')
                })

            return jsonify({
                'success': True,
                'items': items
            })
    finally:
        conn.close()


@app.route('/admin/incidents/bulk-update', methods=['POST'])
def admin_incidents_bulk_update():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    incident_ids = request.form.getlist('incident_ids')
    new_status = request.form.get('new_status', '').strip()
    reject_reason = request.form.get('reject_reason', '').strip()
    return_query = request.form.get('return_query', '').strip()

    if not incident_ids:
        return "<script>alert('선택된 신고가 없습니다.'); history.back();</script>"

    allowed_status = ['처리중', '처리완료', '반려']
    if new_status not in allowed_status:
        return "<script>alert('변경할 상태가 올바르지 않습니다.'); history.back();</script>"

    if new_status == '반려' and not reject_reason:
        return "<script>alert('반려 사유를 입력해주세요.'); history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, latitude, longitude, first_created_at
                FROM incidents
            """)
            raw_incidents = cursor.fetchall()

            raw_incident_map = {str(item['id']): item for item in raw_incidents}

            expanded_ids = set()
            for incident_id in incident_ids:
                target_incident = raw_incident_map.get(str(incident_id))
                if not target_incident:
                    continue

                group_ids = find_group_incident_ids(target_incident, raw_incidents)
                for group_id in group_ids:
                    expanded_ids.add(group_id)

            if not expanded_ids:
                return "<script>alert('처리할 수 있는 신고가 없습니다.'); history.back();</script>"

            expanded_ids = list(expanded_ids)
            placeholders = ', '.join(['%s'] * len(expanded_ids))

            if new_status == '반려':
                sql = f"""
                    UPDATE incidents
                    SET status = %s, reject_reason = %s
                    WHERE id IN ({placeholders})
                """
                params = [new_status, reject_reason] + expanded_ids
            else:
                sql = f"""
                    UPDATE incidents
                    SET status = %s, reject_reason = NULL
                    WHERE id IN ({placeholders})
                """
                params = [new_status] + expanded_ids

            cursor.execute(sql, params)
            conn.commit()

            redirect_url = url_for('admin_incidents')
            if return_query:
                return redirect(f'{redirect_url}?{return_query}')

            return redirect(redirect_url)
    finally:
        conn.close()


@app.route('/admin/members')
def admin_members():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '').strip()
    role = request.args.get('role', '').strip()
    sort = request.args.get('sort', 'role').strip()
    order = request.args.get('order', 'asc').strip().lower()
    per_page = 10

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            where_clauses = []
            params = []

            if keyword:
                where_clauses.append("(name LIKE %s OR uid LIKE %s)")
                like_keyword = f"%{keyword}%"
                params.extend([like_keyword, like_keyword])

            if role:
                where_clauses.append("role = %s")
                params.append(role)

            where_sql = ""
            if where_clauses:
                where_sql = " WHERE " + " AND ".join(where_clauses)

            allowed_sort = ['id', 'name', 'uid', 'role', 'active', 'created_at']
            if sort not in allowed_sort:
                sort = 'role'

            order_sql = 'ASC' if order == 'asc' else 'DESC'

            if sort == 'role':
                if order == 'asc':
                    order_by_sql = """
                        CASE
                            WHEN role = 'admin' THEN 1
                            WHEN role = 'manager' THEN 2
                            WHEN role = 'user' THEN 3
                            ELSE 4
                        END ASC
                    """
                else:
                    order_by_sql = """
                        CASE
                            WHEN role = 'admin' THEN 1
                            WHEN role = 'manager' THEN 2
                            WHEN role = 'user' THEN 3
                            ELSE 4
                        END DESC
                    """
            elif sort == 'active':
                order_by_sql = f"active {order_sql}, id DESC"
            else:
                order_by_sql = f"{sort} {order_sql}"

            count_sql = f"SELECT COUNT(*) AS cnt FROM members{where_sql}"
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['cnt']
            total_pages = (total_count + per_page - 1) // per_page

            if page < 1:
                page = 1

            if total_pages > 0 and page > total_pages:
                page = total_pages

            offset = (page - 1) * per_page

            sql = f"""
                SELECT id, name, uid, role, active, created_at
                FROM members
                {where_sql}
                ORDER BY {order_by_sql}
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [per_page, offset])
            members = cursor.fetchall()

            return render_template(
                'admin_members.html',
                members=members,
                page=page,
                total_pages=total_pages,
                keyword=keyword,
                role=role,
                sort=sort,
                order=order
            )
    finally:
        conn.close()

@app.route('/admin/members/<int:member_id>')
def admin_member_detail(member_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 회원 기본 정보
            member_sql = """
                SELECT
                    id,
                    uid,
                    name,
                    role,
                    active,
                    manager_region,
                    created_at
                FROM members
                WHERE id = %s
            """
            cursor.execute(member_sql, (member_id,))
            member = cursor.fetchone()

            if not member:
                return "<script>alert('존재하지 않는 회원입니다.'); history.back();</script>"

            # 2. 회원 신고 통계 (원본 신고 기준)
            stats_sql = """
                SELECT
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN status = '접수완료' THEN 1 ELSE 0 END) AS received_reports,
                    SUM(CASE WHEN status = '처리중' THEN 1 ELSE 0 END) AS processing_reports,
                    SUM(CASE WHEN status = '처리완료' THEN 1 ELSE 0 END) AS completed_reports,
                    SUM(CASE WHEN status = '반려' THEN 1 ELSE 0 END) AS rejected_reports,
                    SUM(CASE WHEN risk_score >= 70 THEN 1 ELSE 0 END) AS high_risk_reports,
                    SUM(CASE WHEN risk_score >= 40 AND risk_score < 70 THEN 1 ELSE 0 END) AS medium_risk_reports,
                    SUM(CASE WHEN risk_score < 40 THEN 1 ELSE 0 END) AS low_risk_reports,
                    ROUND(AVG(risk_score), 1) AS avg_risk_score,
                    MAX(first_created_at) AS last_report_at
                FROM incidents
                WHERE member_id = %s
            """
            cursor.execute(stats_sql, (member_id,))
            member_stats = cursor.fetchone()

            recent_30d_sql = """
                SELECT COUNT(*) AS recent_30d_reports
                FROM incidents
                WHERE member_id = %s
                  AND first_created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            cursor.execute(recent_30d_sql, (member_id,))
            recent_30d_row = cursor.fetchone()

            member_stats['recent_30d_reports'] = (recent_30d_row.get(
                'recent_30d_reports') if recent_30d_row else 0) or 0

            total_reports = member_stats.get('total_reports') or 0
            completed_reports = member_stats.get('completed_reports') or 0
            rejected_reports = member_stats.get('rejected_reports') or 0
            grouped_reports = member_stats.get('grouped_reports') or 0

            member_stats['approved_rate'] = round((completed_reports / total_reports) * 100,
                                                  1) if total_reports > 0 else 0
            member_stats['rejected_rate'] = round((rejected_reports / total_reports) * 100,
                                                  1) if total_reports > 0 else 0
            member_stats['duplicate_rate'] = round(((total_reports - grouped_reports) / total_reports) * 100,
                                                   1) if total_reports > 0 else 0

            recent_7d_sql = """
                SELECT COUNT(*) AS recent_7d_reports
                FROM incidents
                WHERE member_id = %s
                  AND first_created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            cursor.execute(recent_7d_sql, (member_id,))
            recent_7d_row = cursor.fetchone()

            member_stats['recent_7d_reports'] = (recent_7d_row.get('recent_7d_reports') if recent_7d_row else 0) or 0

            operation_stats_sql = """
                SELECT
                    SUM(CASE WHEN status IN ('접수완료', '처리중') THEN 1 ELSE 0 END) AS pending_reports,
                    SUM(CASE WHEN status IN ('접수완료', '처리중') AND risk_score >= 70 THEN 1 ELSE 0 END) AS high_risk_pending_reports,
                    SUM(CASE WHEN status IN ('접수완료', '처리중')
                             AND first_created_at <= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                             THEN 1 ELSE 0 END) AS long_pending_reports
                FROM incidents
                WHERE member_id = %s
            """
            cursor.execute(operation_stats_sql, (member_id,))
            operation_stats = cursor.fetchone()

            member_stats['pending_reports'] = (operation_stats.get('pending_reports') if operation_stats else 0) or 0
            member_stats['high_risk_pending_reports'] = (operation_stats.get(
                'high_risk_pending_reports') if operation_stats else 0) or 0
            member_stats['long_pending_reports'] = (operation_stats.get(
                'long_pending_reports') if operation_stats else 0) or 0

            # 3. 대표 사건 수 계산용 원본 incident 전체 조회
            group_count_sql = """
                SELECT
                    id,
                    member_id,
                    title,
                    location,
                    region_name,
                    latitude,
                    longitude,
                    image_path,
                    status,
                    reject_reason,
                    risk_score,
                    first_created_at,
                    last_checked_at
                FROM incidents
                WHERE member_id = %s
                ORDER BY first_created_at DESC
            """
            cursor.execute(group_count_sql, (member_id,))
            raw_member_incidents = cursor.fetchall()

            grouped_member_incidents = group_incidents(raw_member_incidents)
            member_stats['grouped_reports'] = len(grouped_member_incidents)
            member_stats['has_rejected_history'] = (member_stats.get('rejected_reports') or 0) > 0

            # 4. 최근 신고 목록 (원본 신고 기준 4개 유지)
            incidents_sql = """
                SELECT
                    id,
                    title,
                    location,
                    region_name,
                    status,
                    risk_score,
                    first_created_at,
                    last_checked_at,
                    reject_reason
                FROM incidents
                WHERE member_id = %s
                ORDER BY first_created_at DESC
                LIMIT 4
            """
            cursor.execute(incidents_sql, (member_id,))
            member_incidents = cursor.fetchall()

            return render_template(
                'admin_member_detail.html',
                member=member,
                member_stats=member_stats,
                member_incidents=member_incidents
            )
    finally:
        conn.close()

@app.route('/admin/members/update-status', methods=['POST'])
def admin_member_update_status():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    member_id = request.form.get('member_id', '').strip()
    active = request.form.get('active', '').strip()

    if not member_id or active not in ['0', '1']:
        return "<script>alert('잘못된 요청입니다.'); history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                UPDATE members
                SET active = %s
                WHERE id = %s
            """
            cursor.execute(sql, (int(active), member_id))
        conn.commit()
        return redirect(url_for('admin_member_detail', member_id=member_id))
    finally:
        conn.close()

@app.route('/admin/members/update-role', methods=['POST'])
def admin_member_update_role():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    member_id = request.form.get('member_id', '').strip()
    role = request.form.get('role', '').strip()

    if not member_id or role not in ['admin', 'manager', 'user']:
        return "<script>alert('잘못된 요청입니다.'); history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                UPDATE members
                SET role = %s
                WHERE id = %s
            """
            cursor.execute(sql, (role, member_id))
        conn.commit()
        return redirect(url_for('admin_member_detail', member_id=member_id))
    finally:
        conn.close()

@app.route('/admin/statistics')
def admin_statistics():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    region_name,
                    location,
                    status,
                    risk_score,
                    first_created_at
                FROM incidents
                ORDER BY first_created_at DESC
            """)
            raw_incidents = cursor.fetchall()

            grouped_incidents = group_incidents(raw_incidents)

            # 1. 전국 > 도/광역시 > 시/군/구 구조
            region_tree = {}

            for incident in grouped_incidents:
                parsed = parse_region_hierarchy(
                    incident.get('region_name'),
                    incident.get('location')
                )

                level1 = parsed.get('level1') or '기타'
                level2 = parsed.get('level2')
                level3 = parsed.get('level3')

                if level1 not in region_tree:
                    region_tree[level1] = {}

                # level2가 없으면 level1 바로 아래에 기타로 집계
                if not level2:
                    region_tree[level1]['기타'] = region_tree[level1].get('기타', 0) + 1
                    continue

                # level2가 있으면 dict 구조 보장
                if level2 not in region_tree[level1]:
                    region_tree[level1][level2] = {}

                # level3가 있으면 3단계까지 집계
                if level3:
                    region_tree[level1][level2][level3] = (
                            region_tree[level1][level2].get(level3, 0) + 1
                    )
                else:
                    # level3가 없으면 level2 자체를 종료 노드로 만들기 위해
                    # '__count__'로 임시 보관
                    region_tree[level1][level2]['__count__'] = (
                            region_tree[level1][level2].get('__count__', 0) + 1
                    )

            # level2 아래에 '__count__'만 있고 실제 하위 구가 없으면 숫자로 평탄화
            normalized_region_tree = {}

            for level1, level2_map in region_tree.items():
                normalized_region_tree[level1] = {}

                for level2, level3_map in level2_map.items():
                    child_keys = [k for k in level3_map.keys() if k != '__count__']

                    if child_keys:
                        normalized_region_tree[level1][level2] = {
                            k: v for k, v in level3_map.items() if k != '__count__'
                        }

                        if level3_map.get('__count__'):
                            normalized_region_tree[level1][level2]['기타'] = (
                                    normalized_region_tree[level1][level2].get('기타', 0)
                                    + level3_map['__count__']
                            )
                    else:
                        normalized_region_tree[level1][level2] = level3_map.get('__count__', 0)

            region_data = {
                '전국': normalized_region_tree
            }

            # 2. 요약 수치
            now = datetime.now()
            today = now.date()

            statistics_summary = {
                'totalReports': len(grouped_incidents),
                'pendingReports': sum(1 for i in grouped_incidents if i.get('status') in ['접수완료', '처리중']),
                'dangerReports': sum(
                    1 for i in grouped_incidents
                    if i.get('status') in ['접수완료', '처리중'] and float(i.get('risk_score') or 0) >= 70
                ),
                'delayedReports': sum(
                    1 for i in grouped_incidents
                    if i.get('status') == '접수완료'
                    and i.get('first_created_at')
                    and (now - i.get('first_created_at')).total_seconds() >= 86400
                ),
                'todayReports': sum(
                    1 for i in grouped_incidents
                    if i.get('first_created_at') and i.get('first_created_at').date() == today
                )
            }

            # ===== 운영 인사이트 생성 =====
            insights = []

            # 1. 장기 지연 우선 경고
            if statistics_summary['delayedReports'] >= 3:
                insights.append(
                    f"24시간 이상 지연된 신고가 {statistics_summary['delayedReports']}건 발생했습니다."
                )

            # 2. 고위험 미처리 경고
            if statistics_summary['dangerReports'] > 0:
                insights.append(
                    f"고위험 미처리 신고 {statistics_summary['dangerReports']}건이 남아 있습니다."
                )

            # 3. 오늘 접수 증가 감지 (간단 기준)
            avg_reports = statistics_summary['totalReports'] / 7 if statistics_summary['totalReports'] else 0

            if statistics_summary['todayReports'] > avg_reports:
                insights.append("오늘 접수량이 평소보다 많은 흐름을 보이고 있습니다.")

            # 4. 이상 징후가 없을 때
            if not insights:
                insights.append("현재 확인된 주요 지연·고위험 이상 징후는 없습니다.")

            # ===== 운영 인사이트 생성 =====
            insights = []

            if statistics_summary['dangerReports'] > 0:
                insights.append(f"고위험 신고 {statistics_summary['dangerReports']}건이 아직 처리되지 않았습니다.")

            if statistics_summary['delayedReports'] >= 3:
                insights.append(f"24시간 이상 지연된 신고가 {statistics_summary['delayedReports']}건 발생했습니다.")

            avg_reports = statistics_summary['totalReports'] / 7 if statistics_summary['totalReports'] else 0

            if statistics_summary['todayReports'] > avg_reports:
                insights.append("오늘 신고량이 최근 평균보다 증가했습니다.")

            if not insights:
                insights.append("현재 특별한 이상 징후는 없습니다.")

            # ===== 운영 인사이트 생성 =====
            insights = []

            # 1. 고위험 미처리
            if statistics_summary['dangerReports'] > 0:
                insights.append(f"고위험 신고 {statistics_summary['dangerReports']}건이 아직 처리되지 않았습니다.")

            # 2. 장기 지연
            if statistics_summary['delayedReports'] >= 3:
                insights.append(f"24시간 이상 지연된 신고가 {statistics_summary['delayedReports']}건 발생했습니다.")

            # 3. 오늘 증가 감지 (간단 기준)
            avg_reports = statistics_summary['totalReports'] / 7 if statistics_summary['totalReports'] else 0

            if statistics_summary['todayReports'] > avg_reports:
                insights.append("오늘 신고량이 최근 평균보다 증가했습니다.")

            # 4. 아무 것도 없을 때
            if not insights:
                insights.append("현재 특별한 이상 징후는 없습니다.")

            # 3. 추이 데이터

            # 최근 7일: 일 단위 고정 7칸
            cursor.execute("""
                SELECT DATE(first_created_at) AS report_date, COUNT(*) AS count
                FROM incidents
                WHERE first_created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
                GROUP BY DATE(first_created_at)
                ORDER BY report_date ASC
            """)
            rows_7d = cursor.fetchall()

            row_7d_map = {
                row['report_date'].strftime('%Y-%m-%d'): int(row['count'])
                for row in rows_7d
            }

            labels_7d = []
            values_7d = []

            for i in range(6, -1, -1):
                target_day = (datetime.now() - timedelta(days=i)).date()
                key = target_day.strftime('%Y-%m-%d')
                labels_7d.append(target_day.strftime('%m-%d'))
                values_7d.append(row_7d_map.get(key, 0))

            # 최근 30일: 주 단위 고정 5칸
            cursor.execute("""
                SELECT YEARWEEK(first_created_at, 1) AS yearweek, COUNT(*) AS count
                FROM incidents
                WHERE first_created_at >= DATE_SUB(CURDATE(), INTERVAL 34 DAY)
                GROUP BY YEARWEEK(first_created_at, 1)
                ORDER BY yearweek ASC
            """)
            rows_30d = cursor.fetchall()

            row_30d_map = {
                str(row['yearweek']): int(row['count'])
                for row in rows_30d
            }

            labels_30d = []
            values_30d = []

            for i in range(4, -1, -1):
                target_day = datetime.now() - timedelta(days=i * 7)
                yearweek = target_day.strftime('%G%V')
                labels_30d.append(f"{5 - i}주")
                values_30d.append(row_30d_map.get(yearweek, 0))

            # 전체: 최근 6개월 고정
            cursor.execute("""
                SELECT DATE_FORMAT(first_created_at, '%Y-%m') AS ym, COUNT(*) AS count
                FROM incidents
                GROUP BY DATE_FORMAT(first_created_at, '%Y-%m')
                ORDER BY ym ASC
            """)
            rows_all = cursor.fetchall()

            row_all_map = {
                row['ym']: int(row['count'])
                for row in rows_all
            }

            labels_all = []
            values_all = []

            now_dt = datetime.now()
            for i in range(5, -1, -1):
                year = now_dt.year
                month = now_dt.month - i

                while month <= 0:
                    month += 12
                    year -= 1

                ym = f"{year}-{month:02d}"
                labels_all.append(f"{month}월")
                values_all.append(row_all_map.get(ym, 0))

            trend_data = {
                '7d': {
                    'labels': labels_7d,
                    'values': values_7d
                },
                '30d': {
                    'labels': labels_30d,
                    'values': values_30d
                },
                'all': {
                    'labels': labels_all,
                    'values': values_all
                }
            }

            return render_template(
                'admin_statistics.html',
                region_data=region_data,
                trend_data=trend_data,
                statistics_summary=statistics_summary,
                insights=insights
            )
    finally:
        conn.close()

@app.route('/incident/update-status', methods=['POST'])
def incident_update_status():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('user_role') != 'admin':
        return redirect(url_for('alert_page'))

    incident_id = request.form.get('incident_id', '').strip()
    new_status = request.form.get('new_status', '').strip()
    reject_reason = request.form.get('reject_reason', '').strip()
    return_query = request.form.get('return_query', '').strip()

    if not incident_id:
        return "<script>alert('사건 정보가 없습니다.'); history.back();</script>"

    allowed_status = ['처리중', '처리완료', '반려']
    if new_status not in allowed_status:
        return "<script>alert('변경할 상태가 올바르지 않습니다.'); history.back();</script>"

    if new_status == '반려' and not reject_reason:
        return "<script>alert('반려 사유를 입력해주세요.'); history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, latitude, longitude, first_created_at
                FROM incidents
                WHERE id = %s
            """, (incident_id,))
            target_incident = cursor.fetchone()

            if not target_incident:
                return "<script>alert('존재하지 않는 사건입니다.'); history.back();</script>"

            cursor.execute("""
                SELECT id, latitude, longitude, first_created_at
                FROM incidents
            """)
            raw_incidents = cursor.fetchall()

            group_ids = find_group_incident_ids(target_incident, raw_incidents)
            placeholders = ', '.join(['%s'] * len(group_ids))

            if new_status == '반려':
                sql = f"""
                    UPDATE incidents
                    SET status = %s, reject_reason = %s
                    WHERE id IN ({placeholders})
                """
                cursor.execute(sql, [new_status, reject_reason] + group_ids)
            else:
                sql = f"""
                    UPDATE incidents
                    SET status = %s, reject_reason = NULL
                    WHERE id IN ({placeholders})
                """
                cursor.execute(sql, [new_status] + group_ids)

            conn.commit()

            redirect_url = url_for('admin_incidents')
            if return_query:
                return redirect(f'{redirect_url}?{return_query}')

            return redirect(redirect_url)
    finally:
        conn.close()


####################################### 게시판 CRUD END #######################################


@app.route('/')
def index():
    return render_template("main.html")


if __name__ == '__main__':
    app.run(host='localhost', port=5001, debug=True)