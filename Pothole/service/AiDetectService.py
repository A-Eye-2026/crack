from common.session import Session

class AiDetectService:
    @staticmethod
    def save_detect_post(member_id, title, content, image_path, result_json):
        conn = Session.get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO ai_detect_posts 
                 (member_id, title, content, image_path, detect_result) 
                 VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (member_id, title, content, image_path, result_json))
        conn.commit()
        cursor.close()

    @staticmethod
    def get_all_posts():
        conn = Session.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_detect_posts ORDER BY id DESC")
        return cursor.fetchall()
        
    @staticmethod
    def delete_post(post_id):
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM ai_detect_posts WHERE id = %s", (post_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"AiDetect DB 삭제 실패: {e}")
            return False
        finally:
            cursor.close()
            conn.close()