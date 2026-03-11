import os
import uuid
from common.session import Session
from domain.Post import Post, Attachment

class PostService:
    #파일 게시물 저장
    @staticmethod
    def save_post(member_id, title, content, files=None, upload_folder='uploads/'):
        """게시글과 첨부파일을 동시에 저장 (트랜잭션 처리)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 게시글 먼저 저장
                sql_post = "INSERT INTO posts (member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql_post, (member_id, title, content))
                # 2. 방금 INSERT된 게시글의 ID(PK) 가져오기
                post_id = cursor.lastrowid

                # 3. 다중 파일 처리 (ImgBB 및 로컬 저장 연동)
                if files:
                    from common.imgbb import upload_to_imgbb
                    
                    for file in files:
                        if file and file.filename != '':
                            origin_name = file.filename
                            ext = origin_name.rsplit('.', 1)[1].lower() if '.' in origin_name else 'bin'
                            
                            # 이미지 여부 확인
                            is_image = ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']
                            
                            public_url = None
                            if is_image:
                                # ImgBB 업로드
                                public_url = upload_to_imgbb(file)
                            
                            # ImgBB 실패하거나 이미지가 아닌 경우 로컬 저장 (Vercel 휘발성 감수)
                            if not is_image or not public_url:
                                save_name = f"{uuid.uuid4().hex}.{ext}"
                                # 로컬 저장 경로 확보
                                if not os.path.exists(upload_folder):
                                    os.makedirs(upload_folder)
                                
                                # file이 이미 읽혔을 수 있으므로 seek(0) 시도 (필요시)
                                if hasattr(file, 'seek'):
                                    file.seek(0)
                                    
                                file_path = os.path.join(upload_folder, save_name)
                                file.save(file_path)
                                public_url = f"/uploads/{save_name}"
                            else:
                                save_name = origin_name

                            sql_file = """INSERT INTO attachments (post_id, origin_name, save_name, file_path)
                                          VALUES (%s, %s, %s, %s)"""
                            cursor.execute(sql_file, (post_id, origin_name, save_name, public_url))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving post: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def get_posts():
        """작성자 이름과 첨부파일 개수를 함께 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                        SELECT p.*, m.name as writer_name,
                                (SELECT COUNT(*) FROM attachments WHERE post_id = p.id) as file_count
                        FROM posts p
                        JOIN members m ON p.member_id = m.id
                        ORDER BY p.created_at DESC
                        """
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [Post.from_db(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_post_detail(post_id):
        """게시글 상세 정보와 첨부파일 함께 조회"""
        conn = Session.get_connection()
        try :
            with conn.cursor() as cursor:
                sql_post = """
                        SELECT p.*, m.name as writer_name
                        FROM posts p
                        JOIN members m ON p.member_id = m.id
                        WHERE p.id = %s
                        """
                cursor.execute(sql_post, (post_id,))
                row = cursor.fetchone()
                post = Post.from_db(row)

                cursor.execute("SELECT * FROM attachments WHERE post_id = %s", (post_id,))
                attachment_rows = cursor.fetchall()
                files = [Attachment.from_db(r) for r in attachment_rows]
                
                conn.commit()
                return post, files
        finally:
            conn.close()

    @staticmethod
    def delete_post(post_id, member_id, user_role=None, upload_folder='uploads/'):
        """게시글 및 관련 실제 파일 삭제 (권한 확인 포함)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 권한 확인
                cursor.execute("SELECT member_id FROM posts WHERE id = %s", (post_id,))
                post = cursor.fetchone()
                if not post:
                    return False
                
                if post['member_id'] != member_id and user_role != 'admin':
                    return False

                cursor.execute("SELECT save_name FROM attachments WHERE post_id = %s", (post_id,))
                files = cursor.fetchall()

                for f in files:
                    file_path = os.path.join(upload_folder, f['save_name'])
                    if os.path.exists(file_path):
                        os.remove(file_path)

                sql = "DELETE FROM posts WHERE id = %s"
                cursor.execute(sql, (post_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Delete Error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def update_post(post_id, title, content, files=None, upload_folder='uploads/'):
        """게시글 수정 및 다중 파일 교체"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s", (title, content, post_id))

                if files and any(f.filename != '' for f in files):
                    cursor.execute("SELECT save_name FROM attachments WHERE post_id = %s", (post_id,))
                    old_files = cursor.fetchall()
                    for old in old_files:
                        old_path = os.path.join(upload_folder, old['save_name'])
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    cursor.execute("DELETE FROM attachments WHERE post_id = %s", (post_id,))

                    from common.imgbb import upload_to_imgbb
                    
                    for file in files:
                        if file and file.filename != '':
                            origin_name = file.filename
                            ext = origin_name.rsplit('.', 1)[1].lower() if '.' in origin_name else 'bin'
                            is_image = ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']
                            
                            public_url = None
                            if is_image:
                                public_url = upload_to_imgbb(file)
                                
                            if not is_image or not public_url:
                                save_name = f"{uuid.uuid4().hex}.{ext}"
                                if not os.path.exists(upload_folder):
                                    os.makedirs(upload_folder)
                                
                                if hasattr(file, 'seek'):
                                    file.seek(0)
                                    
                                file_path = os.path.join(upload_folder, save_name)
                                file.save(file_path)
                                public_url = f"/uploads/{save_name}"
                            else:
                                save_name = origin_name

                            cursor.execute("""
                                    INSERT INTO attachments (post_id, origin_name, save_name, file_path)
                                    VALUES (%s, %s, %s, %s)
                                """, (post_id, origin_name, save_name, public_url))

                conn.commit()
                return True
        except Exception as e:
            print(f"Update Error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def increment_views(post_id):
        """게시글 조회수 증가"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE posts SET view_count = view_count + 1 WHERE id = %s", (post_id,))
                conn.commit()
        finally:
            conn.close()
