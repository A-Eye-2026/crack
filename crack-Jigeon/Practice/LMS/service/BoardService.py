from LMS.domain.Board import Board
from LMS.common.Session import Session

class BoardService:
    @classmethod
    def run(cls):
        if not Session.is_login():
            print("현재 로그인 상태가 아닙니다.")
            return
        while True:
            print(f"\n======== MBC 게시판 ========")
            cls.list_board()
            print("1. 글쓰기")
            print("2. 글 상세보기(수정 및 삭제 가능")
            print("0. 뒤로가기")

            sel = input("선택 : ")
            if sel == "1":
                cls.write_board()
            elif sel == "2":
                cls.view_detail()
            elif sel == "0":
                break
    @classmethod
    def list_board(cls):
        print("\n"+"="*60)
        print(f"{'번호':<5} | {'제목':<25} | {'작성자':<10} | {'작성일'}")
        print("="*60)

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'select b.*,m,name from boards b join members m on b.member_id = m.id order by b.id desc'
                cursor.execute(sql)
                datas = cursor.fetchall()
                for data in datas:
                    data_str = data['created_at'].strftime('%y-%m-%d')
                    print(f"{data['id']:<5} | {data['title']:<25} | {data['name']:<10} | {data_str}")
        finally:
            conn.close()

        print("="*60)
    @classmethod
    def write_board(cls):
        print("\n====새 글 작성====")
        title = input("제목 : ")
        content = input("내용 : ")

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'insert into boards (member_id,title,content) values (%s,%s,%s)'
                cursor.execute(sql,(Session.login_member,title,content))
                conn.commit()
                print("글이 성공적으로 등록되었습니다.")
        finally:
            conn.close()
    @classmethod
    def view_detail(cls):
        board_id = input("조회할 글 번호 : ")
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'select * from boards where board_id = %s'
                cursor.execute(sql,(board_id,))
                row = cursor.fetchone()
                if not row:
                    print("존재하지 않는 글입니다.")
                    return
                print("\n"+"="*40)
                print(f"제목 : {row['title']}"
                      f"작성자 : {row['name']}{row['uid']}"
                      f"작성일 : {row['created_at']}")
                print("="*40)
                print(f"{row['content']}")
                print("="*40)

                if row['member_id'] == Session.login_member.id:
                    print("1. 수정 2.삭제 0.목록으로")
                    sel = input("선택 : ")
                    if sel == "1":
                        cls.update_board(board_id)
                    elif sel == "2":
                        cls.delete_board(board_id)
        finally:
            conn.close()
    @classmethod
    def update_board(cls, board_id):
        new_title = input("수정할 제목 : ")
        new_content = input("수정할 내용 : ")
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'update boards set title = %s, content = %s where board_id = %s'
                cursor.execute(sql,(new_title,new_content,board_id))
                conn.commit()
                print("수정완료!")
        finally:
            conn.close()
    @classmethod
    def delete_board(cls, board_id):
        confirm = input("정말 삭제하시나요? (y/n) : ").lower()
        if not confirm == "y": return

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'delete from boards where board_id = %s'
                cursor.execute(sql,(board_id,))
                conn.commit()
                print("글이 삭제되었습니다.")
        finally:
            conn.close()