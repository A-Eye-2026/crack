from common.session import Session
from domain.Score import Score

class ScoreService:

    @staticmethod
    def get_score_status(target_uid):
        """성적 입력 폼을 위한 데이터 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 학생 정보 조회
                cursor.execute("SELECT id, name FROM members WHERE uid = %s", (target_uid,))
                student = cursor.fetchone()
                if not student:
                    return None, None

                # 기존 성적 조회
                cursor.execute("SELECT * FROM scores WHERE member_id = %s", (student['id'],))
                row = cursor.fetchone()
                score_obj = Score.from_db(row) if row else None
                
                return score_obj, student['name']
        finally:
            conn.close()

    @staticmethod
    def save_score(target_uid, kor, eng, math):
        """학생 성적 저장 (INSERT or UPDATE)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
                student = cursor.fetchone()
                if not student:
                    return False, "존재하지 않는 학생입니다."

                temp_score = Score(member_id=student['id'], kor=kor, eng=eng, math=math)

                # 기존 데이터 유무 확인
                cursor.execute("SELECT id FROM scores WHERE member_id = %s", (student['id'],))
                is_exist = cursor.fetchone()

                if is_exist:
                    sql = """
                        UPDATE scores SET korean=%s, english=%s, math=%s, 
                                          total=%s, average=%s, grade=%s
                        WHERE member_id = %s
                    """
                    cursor.execute(sql, (temp_score.kor, temp_score.eng, temp_score.math,
                                         temp_score.total, temp_score.avg, temp_score.grade,
                                         student['id']))
                else:
                    sql = """
                        INSERT INTO scores (member_id, korean, english, math, total, average, grade)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (student['id'], temp_score.kor, temp_score.eng, temp_score.math,
                                         temp_score.total, temp_score.avg, temp_score.grade))

                conn.commit()
                return True, "성적 저장 완료"
        except Exception as e:
            print(f"Score save error: {e}")
            return False, "저장 중 오류 발생"
        finally:
            conn.close()

    @staticmethod
    def get_all_scores():
        """전체 성적 목록 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT m.name, m.uid, s.*, 
                           DATE_FORMAT(s.created_at, '%y%m%d') as formatted_date
                    FROM scores s
                    JOIN members m ON s.member_id = m.id
                    WHERE m.role = 'user'
                    ORDER BY s.total DESC
                """
                cursor.execute(sql)
                datas = cursor.fetchall()
                
                score_objects = []
                for data in datas:
                    s = Score.from_db(data)
                    s.name = data['name']
                    s.uid = data['uid']
                    s.created_at = data['formatted_date']
                    score_objects.append(s)
                return score_objects
        finally:
            conn.close()

    @staticmethod
    def get_member_list_for_score():
        """성적 입력 대상 학생 목록 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT m.id, m.uid, m.name, s.id AS score_id 
                    FROM members m
                    LEFT JOIN scores s ON m.id = s.member_id
                    WHERE m.role = 'user'
                    ORDER BY m.name ASC
                """
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_my_score(member_id):
        """내 성적 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM scores WHERE member_id = %s", (member_id,))
                row = cursor.fetchone()
                return Score.from_db(row) if row else None
        finally:
            conn.close()