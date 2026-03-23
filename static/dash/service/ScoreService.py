from LMS.common.Session import Session
from LMS.domain.Score import Score

class ScoreService:
    @classmethod
    def load(cls):
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('select count(*) as cnt from members')
                count = cursor.fetchone()['cnt']
                print(f"현 시스템에 등록된 성적은 {count}개 입니다.")
        except:
            print("ScoreService.load()메서드 실행 오류...")
        finally:
            print("데이터베이스 종료...")
            conn.close()
    @classmethod
    def run(cls):
        cls.load()
        if not Session.is_login():
            print("현재 로그인 상태가 압니다.")
            return
        member = Session.login_member
        while True:
            print("[성적 관리 시스템]")
            if member.role in ("member","admin"):
                print("1. 학생 성적 입력 및 수정")
            print("2. 내 성적 조회")
            if member.role == "admin":
                print("3. 전체 성적 조회")
            print("0. 뒤로가기")

            sel = input("선택 : ")
            if sel == "1":
                cls.add_score()
            elif sel == "2":
                cls.view_my_score()
            elif sel == "3":
                cls.view_all()
            elif sel == "0":
                break
    @classmethod
    def add_score(cls):
        print("[성적 입력 및 수정]")
        target_id = input("대상 아이디 : ")
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('select id,name from members where id = ?', (target_id,))
                student = cursor.fetchone()

                if not student:
                    print("학생을 찾을 수 없습니다.")
                    return
                kor = int(input("국어 : "))
                eng = int(input("영어 : "))
                math = int(input("수학 : "))
                temp_score = Score(member_id = student['id'],kor=kor, eng=eng, math=math)
                cursor.execute('select id from scores where id = ?', (target_id,))
                if cursor.fetchone():
                    sql = 'update scores set korean = %s, english = %s, math = %s, total = %s, average = %s, grade = %s where member_id = %s'
                    cursor.execute(sql, (temp_score.kor, temp_score.eng,temp_score.math,temp_score.total,temp_score.avg,temp_score.grade,student['id']))
                else:
                    sql = 'insert into scores (member_id,korean,english,math,total,average,grade) values (%s,%s,%s,%s,%s,%s,%s)'
                    cursor.execute(sql,(student['id'],temp_score.kor,temp_score.eng,temp_score.math,temp_score.total,temp_score.avg,temp_score.grade))
                conn.commit()
                print(f"{student['name']} 학생 성적 등록 완료!")
        except Exception as e:
            print("ScoreService.add_score()메서드 실행오류...", e)
        finally:
            conn.close()
    @classmethod
    def view_my_score(cls):
        member = Session.login_member
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'select * from scores where id = %s'
                cursor.execute(sql, (member.id,))
                data = cursor.fetchone()
                if data:
                    s = Score.from_db(data)
                    cls.print_score(s, member.uid)
                else:
                    print("등록된 성적이 없습니다.")
        finally:
            conn.close()
    @classmethod
    def print_score(cls,s,uid):
        print(f"ID : {uid:<10} |"
              f"국어 : {s.kor:>3} 영어 : {s.eng:>3} | 수학 : {s.math:>3} |"
              f"총점 : {s.total:>3} 평균 : {s.avg:>5.2f} 등급 : {s.grade}")
    @classmethod
    def view_all(cls):
        print("[전체 성적 조회]")
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'select m.uid, s.* from scores join members m on s.member_id = m.id'
                cursor.execute(sql)
                datas = cursor.fetchall()
                for data in datas:
                    s = Score.from_db(data)
                    cls.print_score(s,data['uid'])
        finally:
            conn.close()