import pymysql
import os
import ssl

class Session:

    @staticmethod
    def get_connection():  # 데이터베이스에 연결용 코드
        host = os.environ.get('DB_HOST', '127.0.0.1')
        port = int(os.environ.get('DB_PORT', 3306))
        user = os.environ.get('DB_USER', 'root')
        password = os.environ.get('DB_PASSWORD', '')
        db = os.environ.get('DB_NAME', 'lms_db')
        
        connect_args = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        # TiDB Cloud 등 외부 DB는 SSL 필수
        if host != '127.0.0.1' and host != 'localhost':
            connect_args['ssl'] = {'ca': None}
            connect_args['ssl_verify_cert'] = False
        
        return pymysql.connect(**connect_args)
