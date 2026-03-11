from common.session import Session
import pymysql

class LikeService:
    @staticmethod
    def toggle_like(member_id, post_id, post_type):
        """좋아요 토글 (추가/취소) 및 카운트 업데이트"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 테이블 매핑 (v41: 쿼리를 단순화하고 트리거 활용)
                table_map = {
                    'fashion': ('fashions', 'fashion_id'),
                    'recipe': ('recipes', 'recipe_id'),
                    'interior': ('interiors', 'interior_id'),
                    'car': ('car_curations', 'car_id'),
                    'board': ('boards', 'board_id'),
                    'landmark': ('landmarks', 'landmark_id'),
                    'filesboard': ('posts', 'post_id')
                }
                
                mapping = table_map.get(post_type)
                if not mapping:
                    return False, "잘못된 게시글 타입입니다.", 0
                
                table_name, fk_col = mapping

                # 찜 기록 확인 (post_id, post_type 기준 - 더 범용적이고 확실함)
                cursor.execute(
                    "SELECT id FROM likes WHERE member_id = %s AND post_id = %s AND post_type = %s",
                    (member_id, post_id, post_type)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # 좋아요 취소
                    cursor.execute("DELETE FROM likes WHERE id = %s", (existing['id'],))
                    # [v208] 트리거 미작동 대안: 직접 카운트 감소
                    # [v254] 음수 방지 처리: GREATEST(0, ...) 사용
                    cursor.execute(f"UPDATE {table_name} SET likes_count = GREATEST(0, CAST(likes_count AS SIGNED) - 1) WHERE id = %s", (post_id,))
                    action = "removed"
                else:
                    # 좋아요 추가
                    cursor.execute(
                        f"INSERT INTO likes (member_id, {fk_col}, post_type, post_id) VALUES (%s, %s, %s, %s)",
                        (member_id, post_id, post_type, post_id)
                    )
                    # [v208] 트리거 미작동 대안: 직접 카운트 증가
                    cursor.execute(f"UPDATE {table_name} SET likes_count = likes_count + 1 WHERE id = %s", (post_id,))
                    action = "added"
                
                conn.commit()
                
                # 최신 좋아요 수 조회
                cursor.execute(f"SELECT likes_count FROM {table_name} WHERE id = %s", (post_id,))
                row = cursor.fetchone()
                new_count = row['likes_count'] if row else 0
                
                return True, action, new_count
        except Exception as e:
            if conn: conn.rollback()
            print(f"Toggle Like Error: {e}")
            return False, str(e), 0
        finally:
            if conn: conn.close()

    @staticmethod
    def get_liked_posts(member_id):
        """사용자가 좋아요를 누른 모든 게시글 정보 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 찜한 게시글 목록 (최신순)
                cursor.execute("""
                    SELECT post_id, post_type, created_at 
                    FROM likes 
                    WHERE member_id = %s 
                    ORDER BY created_at DESC
                """, (member_id,))
                likes = cursor.fetchall()
                
                results = []
                for like in likes:
                    p_id = like['post_id']
                    p_type = like['post_type']
                    
                    # 각 타입별 테이블에서 정보 가져오기
                    table_name = {
                        'fashion': 'fashions',
                        'recipe': 'recipes',
                        'interior': 'interiors',
                        'car': 'car_curations',
                        'board': 'boards',
                        'landmark': 'landmarks',
                        'filesboard': 'posts'
                    }.get(p_type)
                    
                    if not table_name: continue
                    
                    # 제목과 이미지(또는 내용 설명) 가져오기
                    if p_type == 'landmark':
                        sql = "SELECT id, title, SUBSTRING_INDEX(image_urls, '\\n', 1) as image_url FROM landmarks WHERE id = %s"
                    elif p_type in ['board', 'filesboard']:
                        sql = f"SELECT id, title, '' as image_url FROM {table_name} WHERE id = %s"
                    else:
                        sql = f"SELECT id, title, image_url FROM {table_name} WHERE id = %s"
                    
                    cursor.execute(sql, (p_id,))
                    post = cursor.fetchone()
                    if post:
                        post['type'] = p_type
                        post['liked_at'] = like['created_at']
                        results.append(post)
                
                return results
        finally:
            if conn: conn.close()

    @staticmethod
    def get_liked_posts_paginated(member_id, limit=10, offset=0):
        """사용자가 좋아요를 누른 게시글을 페이징하여 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 지정된 개수만큼만 가져오기
                cursor.execute("""
                    SELECT post_id, post_type, created_at 
                    FROM likes 
                    WHERE member_id = %s 
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (member_id, int(limit), int(offset)))
                likes = cursor.fetchall()
                
                results = []
                for like in likes:
                    p_id = like['post_id']
                    p_type = like['post_type']
                    
                    table_name = {
                        'fashion': 'fashions', 'recipe': 'recipes', 'interior': 'interiors',
                        'car': 'car_curations', 'board': 'boards', 'landmark': 'landmarks', 'filesboard': 'posts'
                    }.get(p_type)
                    
                    if not table_name: continue
                    
                    if p_type == 'landmark':
                        sql = "SELECT id, title, SUBSTRING_INDEX(image_urls, '\\n', 1) as image_url FROM landmarks WHERE id = %s"
                    elif p_type in ['board', 'filesboard']:
                        sql = f"SELECT id, title, '' as image_url FROM {table_name} WHERE id = %s"
                    else:
                        sql = f"SELECT id, title, image_url FROM {table_name} WHERE id = %s"
                    
                    cursor.execute(sql, (p_id,))
                    post = cursor.fetchone()
                    if post:
                        post['type'] = p_type
                        # datetime 객체를 프론트엔드 호환 포맷으로 변환 -> (m-d H:M)
                        post['liked_at'] = like['created_at'].strftime('%m-%d %H:%M') if like['created_at'] else ''
                        results.append(post)
                
                return results
        finally:
            if conn: conn.close()

    @staticmethod
    def is_liked(member_id, post_id, post_type):
        """특정 사용자가 특정 게시글에 좋아요를 눌렀는지 여부"""
        if not member_id: return False
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM likes WHERE member_id = %s AND post_id = %s AND post_type = %s",
                    (member_id, post_id, post_type)
                )
                return cursor.fetchone() is not None
        finally:
            if conn: conn.close()
