# pip install flask
import hashlib
import os
import re

from flask import Flask, render_template, request, redirect, url_for, session, flash
from common.Session import Session # crack. 제거
from domain import Member # crack. 제거
from service import MemberService # crack. 제거

# 1. 경로 문제 해결을 위해 현재 파일의 절대 경로를 기준으로 설정합니다.
# base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'its_guard_secret_key' # 이 줄이 없으면 세션 에러가 납니다.

UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/login', methods=['GET','POST'])
def login(uid=None):
    if request.method == 'GET':
        return render_template('login.html')

    # 1. 로그인 시도 횟수 세션 초기화 (없을 경우에 '0'으로 설정)
    if 'login_attempts' not in session:
        session['login_attempts'] = 0

    # 2. 이미 로그인 3번 실패했는지 먼저 확인
    if session['login_attempts'] >= 3:
        return "<script>alert(' 3회 이상 로그인 실패로 인해서 접속이 차단되었습니다.');history.back();</script>"

    # 3. 입력값 받기 (여기서부터는 if문 밖으로 나와야 합니다)
    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_conn()
    cursor = conn.cursor()
    try:
        with conn.cursor() as cur:
            sql = 'select id, name, uid, role FROM members WHERE uid = %s and password = %s'
            cursor.execute(sql, (uid, upw))
            user = cursor.fetchone()
            if user:
                # 2. 로그인 성공: 세션에 사용자 정보 저장 및 로그인 3회 실패시 횟수 리셋
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_uid'] = user['uid']
                session['login_attempts'] = 0
                return redirect(url_for('index'))

            else:
                # 로그인 실패 : 횟수 증가
                session['login_attempts'] += 1
                remaining = 3 - session['login_attempts']
                if remaining > 0:
                    return f"<script>alert('아이디 또는 비밀번호가 틀렸습니다. (남은 기회 : {remaining})');history.back();</script>"
                else:
                    return "<script>alert('3회 실패! 이제 로그인이 차단됩니다.');history.back();</script>"
    except Exception as e:
        print(f"로그인 에러 : {e}")
        return "<script>alert('로그인 중 오류가 발생했습니다.');history.back();</script>"
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/join', methods=['GET','POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')
    # 1. 입력 데이터 받기
    uid = request.form.get('uid')  # 이메일(ID)
    upw = request.form.get('upw')  # 비밀번호
    upw_check = request.form.get('upw_check')  # 비밀번호 확인
    uname = request.form.get('uname')  # 이름
    # 값이 없으면 None 또는 빈 문자열이 들어옵니다.
    birth = request.form.get('birth') or None
    addr = request.form.get('addr') or ""

    # 2. 비밀번호 보안 규칙 검사 (글자수 제한 없음 설정)
    pw_pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])"

    if not re.search(pw_pattern, upw):
        return "<script>alert('비밀번호에는 영문, 숫자, 특수문자(!#$@!%)가 각각 포함되어야 합니다.');history.back();</script>"

    # 3. 비밀번호 이중화 확인 (입력한 두 비밀번호가 맞는지)
    if upw != upw_check:
        return "<script>alert('비밀번호가 일치하지 않습니다. 다시 확인해 주세요.');history.back();</script>"

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # 3. 이메일 중복 확인
            # 더 정확한 체크 방법 (데이터의 개수를 세어봄)
            check_sql = "SELECT COUNT(*) as cnt FROM members WHERE uid = %s"
            cur.execute(check_sql, (uid,))
            result = cur.fetchone()
            # result['cnt']가 0보다 크면 이미 존재하는 것
            if result and result['cnt'] > 0:
                return "<script>alert('이미 가입된 이메일 입니다.');history.back();</script>"

            # 4. 회원정보 저장 (주석 해제 및 데이터 매칭), 주석처리 한 이유 : 강사님 MySQL 로 접속을 해놓아서
            # 주석처리해놓았음. db에 email, address 쿼리가 없어서.
            # 필수(uid, upw, uname) + 선택(birth, addr) 총 5개 데이터를 집어넣습니다.
            #sql = """INSERT INTO members (uid, password, name, birth, address)
                                #VALUES (%s, %s, %s, %s, %s)"""
            #cur.execute(sql, (uid, upw, uname, birth, addr))
            #conn.commit()

            # 5. 회원가입 완료 후 로그인 페이지로 이동
            return "<script>alert('회원가입이 완료되었습니다.');location.href='/login';</script>"

    except Exception as e:
        conn.rollback()
        print(f"회원가입 에러 : {e}")
        return "<script>alert('가입 중 오류가 발생했습니다.');history.back();</script>"
    finally:
        conn.close()
######################################################################################################################

@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return "<script>alert('로그인이 필요합니다.');location.href='/login';</script>"
    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # 세션에 저장된 id로 전체 정보 조회
            sql = "SELECT uid, name, birth, address FROM members WHERE uid = %s"
            cur.execute(sql, (session['user_id'],))
            user_info = cur.fetchone()
            return render_template('mypage.html', user_info=user_info)
    finally:
        conn.close()


@app.route('/update', methods=['POST'])
# 개인정보수정, 사용자가 입력한 새로운 정보를 DB에 UPDATE 하는 로직.
# 비밀번호 변경 여부에 따라서 쿼리를 나누는 것이 좋을 것 같아서 나누었음//
def update():
    new_name = request.form.get('new_name')
    new_addr = request.form.get('new_addr')
    new_pw = request.form.get('new_pw')

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            if new_pw: # 비밀번호도 변경할 경우
                sql = "UPDATE members SET naem = %s, address=%s, password=%s WHERE id=%s"
                cur.execute(sql, (new_name, new_addr, new_pw, session['user_id']))
            else: # 비밀번호는 유지 할 경우
                sql = "UPDATE members SET name=%s, address=%s WHERE id=%s"
                cur.execute(sql, (new_name, new_addr, session['user_id']))
            conn.commit()
            session['user_name'] = new_name # 세션 이름 정보도 갱신
            return "<script>alert('개인정보가 수정되었습니다.');location.href='/update';</script>"
    except Exception as e:
        conn.rollback()
        return f"<script>alert('정보 수정 중 오류 발생');history.back();</script>"
    finally:
        conn.close()

@app.route('/withdraw', methods=['POST'])
def withdraw():
    pw_confirm = request.form.get('pw_confirm')

    conn = Session.get_conn()
    try:
        with conn.cursor() as cur:
            # 비밀번호 확인 후 삭제
            sql = "DELETE FROM members WHERE id=%s AND password=%s"
            cur.execute(sql, (session['user_id'], pw_confirm))

            if cur.rowcount > 0: # 실제 삭제된 행이 있다면 성공.
                conn.commit()
                session.clear() # 세션 비우기
                return "<script>alert('그동안 이용해주셔서 감사합니다.');location.href='/';</script>"
            else:
                return "<script>alert('비밀번호가 일치하지 않습니다.');history.back();</script>"
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)