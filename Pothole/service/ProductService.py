from common.session import Session
from domain.item import Item
import pymysql
import pymysql.cursors

class ProductService:

    @staticmethod
    def create_item_from_form(form_data):
        def to_int(val, default=0):
            try:
                return int(val) if val and str(val).strip() else default
            except (ValueError, TypeError):
                return default
                
        return Item(
            code=form_data.get('code'),
            name=form_data.get('name'),
            category=form_data.get('category'),
            price=to_int(form_data.get('price')),
            stock=to_int(form_data.get('stock'))
        )

    @staticmethod
    def calculate_total_stock_value(items):
        """
        보유한 상품 객체 리스트를 받아 전체 재고 자산 가치를 계산합니다.
        (DB 조회가 필요 없으므로 staticmethod가 적합)
        """
        return sum(item.price * item.stock for item in items)

    @staticmethod
    def validate_item_data(data):
        """
        입력 데이터의 유효성을 검사합니다.
        """
        if not data.get('code') or int(data.get('price', 0)) < 0:
            return False
        return True

    @staticmethod
    def get_all_products():
        """전체 상품 및 대표 이미지 조회 (정적 메서드)"""
        conn = Session.get_connection()
        # [v273] 명시적으로 DictCursor 사용하여 데이터 매칭 보장
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            # items(i)와 item_images(img)를 조인하여 대표 이미지만 가져옵니다.
            # active = 1인 상품만 가져오도록 필터링 추가
            query = """
                    SELECT i.*, img.image_path AS main_image
                    FROM items i
                    LEFT JOIN item_images img ON i.id = img.item_id AND img.is_main = 1
                    WHERE i.active = 1
                    ORDER BY i.id DESC
                """
            cursor.execute(query)
            rows = cursor.fetchall()

            # Item 객체 리스트로 변환하여 반환
            return [Item.from_db(row) for row in rows]

        except Exception as e:
            print(f"상품 목록 조회 오류: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def register_product(item_obj, image_paths):
        # 0. 중복 코드 검사
        if ProductService.is_code_exists(item_obj.code):
            return False, "이미 존재하는 상품 코드입니다."

        # 1. 커넥션 가져오기
        conn = Session.get_connection()
        # [v273] 명시적으로 DictCursor 사용하여 데이터 매칭 보장
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            # 3. 상품 정보 저장 (v291: active=1 명시적 설정)
            query = """
                    INSERT INTO items (code, name, category, price, stock, active)
                    VALUES (%s, %s, %s, %s, %s, 1)
                """
            cursor.execute(query, (
                item_obj.code, item_obj.name, item_obj.category,
                item_obj.price, item_obj.stock
            ))

            # 방금 삽입된 item의 id 가져오기
            item_id = cursor.lastrowid

            # 4. 이미지 경로 저장
            if image_paths:
                img_query = "INSERT INTO item_images (item_id, image_path, is_main) VALUES (%s, %s, %s)"

                for i, path in enumerate(image_paths):
                    is_main = 1 if i == 0 else 0
                    cursor.execute(img_query, (item_id, path, is_main))

            # 5. 성공 시 커밋
            conn.commit()
            return True, "상품 등록 성공"

        except Exception as e:
            conn.rollback()
            print(f"등록 오류 상세: {e}")
            return False, f"등록 중 오류가 발생했습니다: {str(e)}"

        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def is_code_exists(code):
        """상품 코드 중복 확인"""
        conn = Session.get_connection()
        # [v273] 명시적으로 DictCursor 사용하여 데이터 매칭 보장
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT id FROM items WHERE code = %s", (code,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_product_by_id(item_id):
        """상품 상세 정보 및 모든 이미지 조회"""
        conn = Session.get_connection()
        # [v273] 명시적으로 DictCursor 사용하여 데이터 매칭 보장
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            # 1. 상품 기본 정보 가져오기
            cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
            item_row = cursor.fetchone()

            if not item_row:
                return None

            # 2. 해당 상품의 모든 이미지 경로 가져오기 (is_main 순서대로 정렬)
            cursor.execute("""
                SELECT image_path, is_main 
                FROM item_images 
                WHERE item_id = %s ORDER BY is_main DESC, id ASC""", (item_id,))
            image_rows = cursor.fetchall()

            # 이미지 경로들만 리스트로 추출
            image_list = [row['image_path'] for row in image_rows]

            # [중요] 대표 이미지(main_image)를 명시적으로 row에 넣어줍니다.
            # is_main=1인 이미지가 있다면 그 녀석을, 없다면 첫 번째 이미지를 사용합니다.
            main_img = next((row['image_path'] for row in image_rows if row['is_main'] == 1), None)
            if not main_img and image_list:
                main_img = image_list[0]

            item_row['main_image'] = main_img  # 이 값이 있어야 Item.from_db에서 인식함!
            return Item.from_db(item_row, images=image_list)

        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def soft_delete_product(item_id):
        """상품 소프트 삭제 (active = 0)"""
        conn = Session.get_connection()
        # [v273] 명시적으로 DictCursor 사용하여 데이터 매칭 보장
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("UPDATE items SET active = 0 WHERE id = %s", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"상품 삭제(소프트) 에러: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_stock(item_id, new_stock):
        """상품 재고 수정 (관리자용)"""
        conn = Session.get_connection()
        # [v273] 명시적으로 DictCursor 사용하여 데이터 매칭 보장
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("UPDATE items SET stock = %s WHERE id = %s", (new_stock, item_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"재고 수정 에러: {e}")
            return False
        finally:
            cursor.close()
            conn.close()