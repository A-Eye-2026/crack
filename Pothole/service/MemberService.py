from common.session import Session
from domain.Member import Member
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

class MemberService:

    @staticmethod
    def login(uid, upw):
        """웹 로그인용: 사용자 정보 반환 (딕셔너리 형태)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 먼저 아이디로 사용자 조회
                sql = "SELECT id, name, uid, password, role FROM members WHERE uid = %s"
                cursor.execute(sql, (uid,))
                user = cursor.fetchone()
                
                # 2. 비밀번호 해시 검증
                if user and check_password_hash(user['password'], upw):
                    # 세션에 불필요한 비밀번호 정보는 제외한 딕셔너리 반환
                    return {
                        'id': user['id'],
                        'name': user['name'],
                        'uid': user['uid'],
                        'role': user['role']
                    }
                return None
        finally:
            conn.close()

    @staticmethod
    def signup(uid, password, name):
        """웹 회원가입용: 성공 여부와 메시지 반환"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 중복 체크
                cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
                if cursor.fetchone():
                    return False, "이미 존재하는 아이디입니다."

                # 비밀번호 해싱
                hashed_pw = generate_password_hash(password)
                
                sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
                cursor.execute(sql, (uid, hashed_pw, name))
                conn.commit()
                return True, "회원가입이 완료되었습니다."
        except Exception as e:
            print(f"Signup error: {e}")
            return False, "가입 중 오류가 발생했습니다."
        finally:
            conn.close()

    @staticmethod
    def google_login_or_signup(uid, email, name, profile_photo=None):
        """구글 로그인 및 자동 회원가입 로직"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 이미 존재하는 회원인지 확인 (구글 UID = DB의 uid 컬럼에 매핑)
                cursor.execute("SELECT id, name, uid, role, email FROM members WHERE uid = %s", (uid,))
                user = cursor.fetchone()
                
                if user:
                    # 기존 유저지만 email이 없으면 업데이트
                    if email and not user.get('email'):
                        cursor.execute("UPDATE members SET email = %s WHERE uid = %s", (email, uid))
                        conn.commit()
                    return user
                
                # 2. 신규 회원이면 자동 가입 (비밀번호는 소셜로그인용 더미 텍스트)
                sql = "INSERT INTO members (uid, password, name, profile_photo, email) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (uid, 'google_oauth_dummy', name, profile_photo, email))
                conn.commit()
                
                # 3. 방금 가입한 유저 정보 다시 조회
                cursor.execute("SELECT id, name, uid, role FROM members WHERE uid = %s", (uid,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def kakao_login_or_signup(kakao_id, nickname, profile_photo=None, email=None):
        """카카오 로그인 및 자동 회원가입 로직"""
        conn = Session.get_connection()
        uid = f"kakao:{kakao_id}"
        try:
            with conn.cursor() as cursor:
                # 1. 이미 존재하는 회원인지 확인
                cursor.execute("SELECT id, name, uid, role, active, email FROM members WHERE uid = %s", (uid,))
                user = cursor.fetchone()
                
                if user:
                    # 기존 유저지만 email이 없으면 업데이트
                    if email and not user.get('email'):
                        cursor.execute("UPDATE members SET email = %s WHERE uid = %s", (email, uid))
                        conn.commit()
                    return user
                
                # 2. 신규 회원이면 자동 가입
                sql = "INSERT INTO members (uid, password, name, profile_photo, role, email) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (uid, 'kakao_oauth_dummy', nickname, profile_photo, 'user', email))
                conn.commit()
                
                # 3. 방금 가입한 유저 정보 다시 조회
                cursor.execute("SELECT id, name, uid, role, active FROM members WHERE uid = %s", (uid,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Kakao Login error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_member_info_by_uid(uid):
        """UID로 회원 정보 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM members WHERE uid = %s", (uid,))
                return cursor.fetchone()
        finally:
            conn.close()


    @staticmethod
    def get_member_info(member_id):
        """회원 정보 조회 (Member 객체 반환)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
                row = cursor.fetchone()
                return Member.from_db(row)
        finally:
            conn.close()

    @staticmethod
    def update_member(member_id, name, password=None):
        """회원 정보 수정"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                if password:
                    hashed_pw = generate_password_hash(password)
                    sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                    cursor.execute(sql, (name, hashed_pw, member_id))
                else:
                    sql = "UPDATE members SET name = %s WHERE id = %s"
                    cursor.execute(sql, (name, member_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Update error: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_board_count(member_id):
        """사용자가 작성한 게시글 개수 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s", (member_id,))
                return cursor.fetchone()['board_count']
        finally:
            conn.close()

    @staticmethod
    def get_my_activity_summary(member_id):
        """마이페이지용 활동 요약 데이터 조회 (v284: 단일 통합 쿼리 최적화)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # [Optimization] 3개의 COUNT(*) 쿼리를 하나로 통합하여 DB 왕복 횟수 감소
                sql = """
                    SELECT 
                        (SELECT COUNT(*) FROM boards WHERE member_id = %s) as board_cnt,
                        (SELECT COUNT(*) FROM posts WHERE member_id = %s) as post_cnt,
                        (SELECT COUNT(*) FROM orders WHERE member_id = %s AND is_hidden = 0) as order_cnt
                """
                cursor.execute(sql, (member_id, member_id, member_id))
                row = cursor.fetchone()

                return {
                    'board_count': row['board_cnt'] if row else 0,
                    'post_count': row['post_cnt'] if row else 0,
                    'order_count': row['order_cnt'] if row else 0,
                    'item_count': 0 # 현재 미사용
                }
        except Exception as e:
            print(f"Activity summary error: {e}")
            return {
                'board_count': 0,
                'post_count': 0,
                'order_count': 0,
                'item_count': 0
            }
        finally:
            conn.close()

    @staticmethod
    def update_photos(member_id, profile_photo=None, cover_photo=None):
        """프로필/커버 사진 업데이트"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                updates = []
                params = []
                if profile_photo is not None:
                    updates.append("profile_photo = %s")
                    params.append(profile_photo)
                if cover_photo is not None:
                    updates.append("cover_photo = %s")
                    params.append(cover_photo)
                if not updates:
                    return True
                params.append(member_id)
                sql = f"UPDATE members SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(sql, params)
                conn.commit()
                return True
        except Exception as e:
            print(f"Photo update error: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def update_last_active(member_id):
        """회원 마지막 활동 시간 갱신"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE members SET last_active = CURRENT_TIMESTAMP WHERE id = %s"
                cursor.execute(sql, (member_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Update last_active error: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_all_members():
        """모든 회원 정보 조회 (카드 뷰용, 온라인 상태 포함)"""
        conn = Session.get_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 1. 5분 이내 활동 여부(is_online)를 포함하여 조회
                sql = """
                    SELECT id, uid, name, profile_photo, cover_photo, role, active, created_at, last_active,
                    CASE WHEN last_active >= NOW() - INTERVAL 5 MINUTE THEN 1 ELSE 0 END as is_online
                    FROM members 
                    ORDER BY created_at DESC
                """
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def toggle_active(member_id):
        """회원 활성화/비활성화 상태 토글"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 현재 상태 조회
                cursor.execute("SELECT active FROM members WHERE id = %s", (member_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "존재하지 않는 회원입니다."
                
                new_status = 0 if row['active'] == 1 else 1
                cursor.execute("UPDATE members SET active = %s WHERE id = %s", (new_status, member_id))
                conn.commit()
                return True, "상태가 변경되었습니다."
        except Exception as e:
            print(f"Toggle active error: {e}")
            return False, "처리에 실패했습니다."
        finally:
            conn.close()