from common.session import Session


class OrderService:
    @staticmethod
    def create_order(member_id, item_id, quantity):
        conn = Session.get_connection()
        cursor = conn.cursor()

        try:
            # 1. 재고 확인 및 상품 가격 가져오기
            cursor.execute("SELECT price, stock FROM items WHERE id = %s FOR UPDATE", (item_id,))
            item = cursor.fetchone()

            if not item or item['stock'] < quantity:
                return False, "재고가 부족합니다."

            # 2. orders 테이블 삽입 (총 금액 계산: 가격 * 수량)
            total_price = item['price'] * quantity
            cursor.execute(
                "INSERT INTO orders (member_id, total_price) VALUES (%s, %s)",
                (member_id, total_price)
            )
            order_id = cursor.lastrowid

            # 3. order_items 테이블 삽입
            cursor.execute(
                "INSERT INTO order_items (order_id, item_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, item_id, quantity, item['price'])
            )

            # 4. 재고 차감 (매우 중요!)
            cursor.execute(
                "UPDATE items SET stock = stock - %s WHERE id = %s",
                (quantity, item_id)
            )

            # 모든 작업 성공 시 확정
            conn.commit()
            return True, "주문이 완료되었습니다."

        except Exception as e:
            conn.rollback()
            print(f"주문 에러: {e}")
            return False, "주문 처리 중 오류가 발생했습니다."
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def cancel_order(order_id, member_id):
        """주문 취소 및 재고 복구"""
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            # 1. 본인의 주문인지 확인 및 상태 확인 (FOR UPDATE)
            cursor.execute("SELECT id, status FROM orders WHERE id = %s AND member_id = %s FOR UPDATE", (order_id, member_id))
            order = cursor.fetchone()
            
            if not order:
                return False, "주문을 찾을 수 없습니다."
            if order['status'] == '주문취소':
                return False, "이미 취소된 주문입니다."

            # 2. 주문한 상품들과 수량 가져오기
            cursor.execute("SELECT item_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
            items = cursor.fetchall()

            # 3. 재고 복구
            for item in items:
                cursor.execute("UPDATE items SET stock = stock + %s WHERE id = %s", (item['quantity'], item['item_id']))

            # 4. 주문 상태 변경
            cursor.execute("UPDATE orders SET status = '주문취소' WHERE id = %s", (order_id,))

            conn.commit()
            return True, "주문이 취소되었습니다."
        except Exception as e:
            conn.rollback()
            print(f"주문 취소 에러: {e}")
            return False, "주문 취소 처리 중 오류가 발생했습니다."
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_order_info(order_id, member_id):
        """주문 상세 정보 조회"""
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            # 주문 기본 정보 (members JOIN으로 주문자 정보 포함)
            cursor.execute("""
                SELECT o.*, m.name AS member_name, m.uid AS member_uid
                FROM orders o
                JOIN members m ON o.member_id = m.id
                WHERE o.id = %s AND o.member_id = %s
            """, (order_id, member_id))
            order = cursor.fetchone()
            if not order:
                return None
            
            # 주문 상품 상세
            query = """
                SELECT oi.*, i.name AS item_name, i.code AS item_code,
                       (SELECT image_path FROM item_images WHERE item_id = i.id AND is_main = 1 LIMIT 1) AS main_image
                FROM order_items oi
                JOIN items i ON oi.item_id = i.id
                WHERE oi.order_id = %s
            """
            cursor.execute(query, (order_id,))
            order['order_items'] = cursor.fetchall()
            return order
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_member_orders(member_id):
        """사용자의 주문 내역 조회"""
        conn = Session.get_connection()
        cursor = conn.cursor()

        try:
            # orders와 order_items, items, members를 조인하여 주문 내역과 상품/주문자 정보를 한꺼번에 가져옴
            query = """
                SELECT 
                    o.id AS order_id,
                    o.total_price,
                    o.status,
                    o.created_at AS order_date,
                    oi.quantity,
                    oi.price AS unit_price,
                    i.name AS item_name,
                    i.id AS item_id,
                    m.name AS member_name,
                    m.uid AS member_uid,
                    (SELECT image_path FROM item_images WHERE item_id = i.id AND is_main = 1 LIMIT 1) AS main_image
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN items i ON oi.item_id = i.id
                JOIN members m ON o.member_id = m.id
                WHERE o.member_id = %s AND o.is_hidden = 0
                ORDER BY o.created_at DESC
            """
            cursor.execute(query, (member_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"주문 내역 조회 오류: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def hide_order(order_id, member_id):
        """주문 내역 숨기기 (소프트 삭제)"""
        conn = Session.get_connection()
        cursor = conn.cursor()
        try:
            # 본인의 주문인지 확인
            cursor.execute("SELECT id FROM orders WHERE id = %s AND member_id = %s", (order_id, member_id))
            order = cursor.fetchone()
            if not order:
                return False, "주문을 찾을 수 없습니다."

            cursor.execute("UPDATE orders SET is_hidden = 1 WHERE id = %s", (order_id,))
            conn.commit()
            return True, "주문 내역이 숨김 처리되었습니다."
        except Exception as e:
            conn.rollback()
            print(f"주문 숨김 에러: {e}")
            return False, "주문 숨김 처리 중 오류가 발생했습니다."
        finally:
            cursor.close()
            conn.close()