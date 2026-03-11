from datetime import datetime, timedelta
import os
from flask import request, session
from common.session import Session
import pymysql
import hashlib

class ViewTracker:
    @staticmethod
    def get_client_ip():
        """클라이언트 IP 주소 획득"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0]
        return request.remote_addr

    @staticmethod
    def hash_ip(ip_address):
        """IP 주소를 SHA-256으로 해싱 (Salt를 추가하여 보안 강화)"""
        salt = os.environ.get('FLASK_SECRET_KEY', 'default_salt')
        combined = ip_address + salt
        return hashlib.sha256(combined.encode()).hexdigest()


    @staticmethod
    def check_and_track_view(item_type, item_id=None):
        """
        조회수 증가 가능 여부를 확인하고 로그를 기록함.
        30분 이내에 동일한 IP(해시) 또는 회원이 동일한 항목을 조회했는지 체크.
        
        Returns:
            bool: 조회수 증가가 필요한 경우 True, 아니면 False
        """
        raw_ip = ViewTracker.get_client_ip()
        ip_hash = ViewTracker.hash_ip(raw_ip)
        member_id = session.get('user_id')
        
        # 1. 쿠키 체크 (app.py에서 처리하지만 2중 방어)
        cookie_name = f'viewed_{item_type}'
        if item_id:
            cookie_name += f'_{item_id}'
            
        if request.cookies.get(cookie_name):
            return False

        # 2. DB 로그 체크 (최근 30분)
        conn = Session.get_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 방문 인정 시간을 12시간으로 연장 (v272)
                time_threshold = (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
                
                if member_id:
                    check_sql = """
                        SELECT id FROM view_logs 
                        WHERE item_type = %s AND item_id <=> %s 
                        AND (member_id = %s OR ip_address = %s)
                        AND viewed_at > %s
                        LIMIT 1
                    """
                    cursor.execute(check_sql, (item_type, item_id, member_id, ip_hash, time_threshold))
                else:
                    check_sql = """
                        SELECT id FROM view_logs 
                        WHERE item_type = %s AND item_id <=> %s 
                        AND ip_address = %s
                        AND viewed_at > %s
                        LIMIT 1
                    """
                    cursor.execute(check_sql, (item_type, item_id, ip_hash, time_threshold))
                
                if cursor.fetchone():
                    return False

                # 3. 로그 기록 (원본 IP 대신 해시 저장)
                log_sql = """
                    INSERT INTO view_logs (item_type, item_id, member_id, ip_address)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(log_sql, (item_type, item_id, member_id, ip_hash))
                conn.commit()
                return True
        except Exception as e:
            print(f"ViewTracker Error: {e}")
            return False
        finally:
            conn.close()

