import json

from common.session import Session

class AiVideoService:
    @staticmethod
    def create_video_post(member_id, title, content, origin_path):
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                INSERT INTO ai_video_posts (member_id, title, content, origin_video_path, status)
                VALUES (%s, %s, %s, %s, 'PENDING')
            """
            cursor.execute(sql, (int(member_id), title, content, origin_path))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"Video DB 저장 실패: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def save_video_detail(video_post_id, frame_num, objects_json):
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            sql = "INSERT INTO ai_video_details (video_post_id, frame_number, detected_objects) VALUES (%s, %s, %s)"
            cursor.execute(sql, (video_post_id, frame_num, json.dumps(objects_json)))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_video_status(video_id, status, result_path, total_frames):
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                    UPDATE ai_video_posts 
                    SET status = %s, result_video_path = %s, total_frames = %s 
                    WHERE id = %s
                """
            cursor.execute(sql, (status, result_path, total_frames, video_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_video_post(post_id):
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            # Foreign Key Constraint CASCADE 설정 상태에 따라 details도 함께 지워지거나 명시적으로 지워야함
            cursor.execute("DELETE FROM ai_video_details WHERE video_post_id = %s", (post_id,))
            cursor.execute("DELETE FROM ai_video_posts WHERE id = %s", (post_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"AiVideo DB 삭제 실패: {e}")
            return False
        finally:
            cursor.close()
            conn.close()