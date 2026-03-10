import pymysql
class Session:
    login_member = None
    @staticmethod
    def get_connection():
        print("get_connection()메서드 호출 - mysql에 접속합니다...")

        return pymysql.connect(
            host='192.168.0.164',
            user='kkk',
            password='1234',  # 본인의 비밀번호로 변경
            db='mbc',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
            # dict 타입으로 처리함 (딕셔너리타입 k : v )
        )
    @classmethod
    def login(cls,member):
        cls.login_member = member
    @classmethod
    def logout(cls):
        cls.login_member = None
    @classmethod
    def is_login(cls):
        return cls.login_member is not None
    @classmethod
    def is_admin(cls):
        return cls.is_login() and cls.login_member.role == "admin"
    @classmethod
    def is_manager(cls):
        return cls.is_login() and cls.login_member.role in ("manager","admin")