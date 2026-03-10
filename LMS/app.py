# pip install flask
# 플라스크란?
# 파이썬으로 만든 db연동 콘솔 프로그램을 웹으로 연결하는 프레임워크
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 것
# app.py 는 플라스크로 서버를 동작하기 위한 파일명 (기본파일)
# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
# static : 정적 파일을 모아놓는 곳 (html, css, js)
# templates : 동적 파일을 모아놓는 곳 (crud 화면, 레이아웃, index 등..)

import os
from flask import Flask,render_template,request,redirect,url_for,session,send_from_directory
from LMS.common.Session import Session
from LMS.domain import *
from LMS.service import *
#                플라스크    프론트 연결      요청,응답  주소전달   주소생성  상태저장

app = Flask(__name__)
app.secret_key = '1234'

@app.route('/login',methods=['GET','POST'])
    # methods는 웹의 동작에 관여한다
    # GET : URL 주소로 데이터를 처리 (보안상 좋지 않음, 대신 빠름)
    # POST : BODY 영역의 데이터를 처리 (보안상 좋음, 대용량일 때 많이 사용됨)
    # 대부분 처음에 화면(HTML 랜더)을 요청할 때는 GET 방식 처리 ----- 로그인 화면 출력 할 때
    # 화면에 있는 내용을 백앤드로 전달할 때는 POST 방식 처리 ----- 로그인 정보를 데이터베이스에 확인할 때
def login():
    if request.method == 'GET':
        return render_template('login.html')
        # GET 방식으로 요청하면 login,html 화면이 나옴
    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = 'SELECT id,name,uid,role FROM members WHERE uid = %s and password = %s'
            #                                                 uid와 password가 동일한지
            #             id,name,uid,role을 가져옴
            cursor.execute(sql,(uid,upw))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_uid'] = user['uid']
                session['user_role'] = user['role']

                return redirect(url_for('index'))
            else:
                return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.');history.back();</script>"
    finally:
        conn.close()
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
@app.route('/join',methods=['GET','POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')
    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디입니다.');history.back();</script>"
            sql = "INSERT INTO members (uid,password,name) VALUES (%s,%s,%s)"
            cursor.execute(sql,(uid,password,name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다.');location.href='/login';</script>"
    except Exception as e:
        print(f"회원가입 오류 : {e}")
        return "가입 중 오류가 발생했습니다. \n join()메서드를 확인하세요."
    finally:
        conn.close()
@app.route('/member/edit',methods=['GET','POST'])
def member_edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html',user=user_info)
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw:
                sql = 'UPDATE members SET name = %s, password = %s WHERE id = %s'
                cursor.execute(sql,(new_name,new_pw,session['user_id']))
            else:
                sql = 'UPDATE members SET name = %s WHERE id = %s'
                cursor.execute(sql,(new_name,session['user_id']))

            conn.commit()
            session['user_name'] = new_name
            return "<script>alert('정보가 수정되었습니다.');location.href='/mypage';</script>"
    except Exception as e:
        print(f"회원수정 오류 : {e}")
        return "수정 중 오류가 발생했습니다. \n member_edit()메서드를 확인하세요."
    finally:
        conn.close()
@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) AS board_count FROM boards where member_id = %s', (session['user_id'],))
            board_count = cursor.fetchone()['board_count']

            return render_template('mypage.html',user=user_info,board_count=board_count)
    finally:
        conn.close()
######################################## 회원 CRUD ####################################################################

####################################### 게시판 CRUD ####################################################################
@app.route('/board/write',methods=['GET','POST']) # http://localhost:5000/board/write
def board_write():
    # 1. 사용자가 '글쓰기' 버튼을 눌러서 들어왔을 때 (화면 보여주기)
    if request.method == 'GET':
        # 로그인 체크 (로그인 안 했으면 글 못 쓰게)
        if 'user_id' not in session:
            return '<script>alert("로그인 후 이용 가능합니다.");location.href="/login";</script>'
        return render_template('board_write.html')
    elif request.method == 'POST': # <form action="/board/write" method="POST">
        title = request.form.get('title')
        content = request.form.get('content')
        # 세션에 저장된 로그인 유저의 id (member_id)
        member_id = session.get('user_id')

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = 'INSERT INTO boards (member_id,title,content) VALUES (%s,%s,%s)'
                cursor.execute(sql,(member_id,title,content))
                conn.commit()
            return redirect(url_for('board_list')) # 저장 후 목록으로 이동
        except Exception as e:
            print(f"글쓰기 에러 : {e}")
            return "저장 중 에러가 발생했습니다."
        finally:
            conn.close()

@app.route('/board') # http:/localhost:5000/board
def board_list():
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 작성자 이름을 함께 가져오기 위해 JOIN 사용
            sql = """
            SELECT b.*, m.name as writer_name
            FROM boards b
            JOIN members m ON b.member_id = m.id
            ORDER BY b.id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            boards = [Board.from_db(row) for row in rows]
            return render_template('board_list.html',boards=boards)
    finally:
        conn.close()

# 2. 게시글 자세히 보기
@app.route('/board/view/<int:board_id>') # http://localhost:5000/board/view/(게시물번호)
def board_view(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # JOIN을 통해 작성자 정보(name, uid)를 함께 조회
            sql = """
            SELECT b.*, m.name as writer_name, m.uid as writer_uid
            FROM boards b
            JOIN members m ON b.member_id = m.id
            WHERE b.id = %s
            """
            cursor.execute(sql, (board_id,))
            row = cursor.fetchone()
            print(row) # db에서 나온 dict타입 콘솔에 출력 테스트용
            if not row:
                return "<script>alert('존재하지 않는 게시글입니다.');history.back()</script>"
            # Boards 객체로 변환 (앞서 작성한 Boards.py의 from_db 활용)
            board = Board.from_db(row)

            return render_template('board_view.html',board=board)
    finally:
        conn.close()
@app.route('/board/edit/<int:board_id>',methods=['GET','POST'])
def board_edit(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 화면 보여주기 (기존 데이터 로드)
            if request.method == 'GET':
                sql = "SELECT * FROM boards WHERE id = %s"
                cursor.execute(sql,(board_id,))
                row = cursor.fetchone()

                if not row:
                    return "<script>alert('존재하지 않는 게시글입니다.');history.back()</script>"

                # 본인 확인 로직 (필요시 추가)
                if row['member_id'] != session.get('user_id'):
                    return "<script>alert('수정 권한이 없습니다.');history.back()</script>"
                print(row) # 콘솔에 출력 테스트용
                board = Board.from_db(row)
                return render_template('board_edit.html',board=board)

            # 2. 실제 DB 업데이트 처리
            elif request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')

                sql = "UPDATE boards SET title = %s, content = %s WHERE id = %s"
                cursor.execute(sql,(title,content,board_id))
                conn.commit()

                return redirect(url_for('board_view',board_id=board_id))
    finally:
        conn.close()

@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = 'DELETE FROM boards WHERE id = %s AND member_id = %s'
            cursor.execute(sql,(board_id,session['user_id']))
            conn.commit()

            if cursor.rowcount > 0:
                print(f"게시글 {board_id}번 삭제 성공")
                return redirect(url_for('board_list'))
            else:
                return "<script>alert('삭제할 수 없습니다.');history.back()</script>"
    except Exception as e:
        print(f"삭제 에러 : {e}")
        return "삭제 중 오류가 발생했습니다."
    finally:
        conn.close()

####################################### 게시판 CRUD END ################################################################

####################################### 성적 CRUD START ################################################################

# 주의사항 : Role에 admin과 manager만 CUD를 제공
# 일반 사용자는 user이고 자신의 성적만 볼 수 있음

@app.route('/score/add') # http://localhost:5000/score/add?uid=test1&name=test1
def score_add():
    if session.get('user_role') not in ('admin','manager'):
        return "<script>alert('권한이 없습니다.');history.back()</script>"

    # request.args는 url을 통해 넘어오는 값, 주소뒤 ?key=value&key=value&....
    target_uid = request.args.get('uid')
    target_name = request.args.get('name')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1, 대상 학생의 id 찾기
            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()

            # 2. 기존 성적이 있는지 조회
            existing_score = None
            if student:
                cursor.execute("SELECT * FROM scores WHERE member_id = %s", (student['id'],))
                row = cursor.fetchone()
                print(row)
                if row:
                    # 기존에 만든 Score.from_db 활용
                    existing_score = Score.from_db(row)
                    # 위쪽에 domain.Score import 할 것

            return render_template('score_form.html',
                                   target_uid=target_uid,
                                   target_name=target_name,
                                   score=existing_score)
    finally:
        conn.close()

@app.route('/score/save', methods=['POST'])
def score_save():
    if session.get('user_role') not in ('admin','manager'):
        return "권한 오류", 403
        # 웹페이지를 오류 페이지로 교체

    # 폼 데이터 수집
    target_uid = request.form.get('target_uid')
    kor = int(request.form.get('korean',0))
    eng = int(request.form.get('english',0))
    math = int(request.form.get('math',0))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 대상 학생의 id(PK) 가져오기 -> 학생의 번호를 가져옴
            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()
            print(student) # 학번 출력
            if not student:
                return "<script>alert('존재하지 않는 학생입니다.');history.back()</script>"

            # 2. Score 객체 생성 (계산 프로퍼티 활용)
            temp_score = Score(member_id=student.get('id'),kor=kor,eng=eng,math=math)
            #               __init__ 를 활용하여 객체 생성

            # 3. 기존 데이터가 있는지 확인
            cursor.execute("SELECT id FROM scores WHERE member_id = %s", (student['id'],))
            is_exist = cursor.fetchone()

            if is_exist: # 성적이 있으면
                # UPDATE 실행
                sql = """
                UPDATE scores SET korean=%s, english=%s, math=%s,
                                  total=%s, average=%s, grade=%s 
                WHERE member_id = %s
                """
                cursor.execute(sql, (temp_score.kor, temp_score.eng, temp_score.math,
                                     temp_score.total, temp_score.avg, temp_score.grade,
                                     student['id']))
            else: # 성적이 없으면
                # INSERT 실행
                sql = """
                    INSERT INTO scores (member_id, korean, english, math, total, average, grade)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (student['id'], temp_score.kor, temp_score.eng, temp_score.math,
                                     temp_score.total, temp_score.avg, temp_score.grade))
                conn.commit()
                return f"<script>alert('{target_uid} 학생 성적 저장 완료!');location.href='/score/list';</script>"
    finally:
        conn.close()

@app.route('/score/list') # http://localhost:5000/score/list -> GET 방식
def score_list():
    # 1. 권한 체크 (관리자나 매니저만 볼 수 있게 설정)
    if session.get('user_role') not in ('admin','manager'):
        return "<script>alert('권한이 없습니다.');history.back()</script>"
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 2. JOIN을 사용하여 학생 이름(name)과 성적 데이터를 함께 조회
            # 성적이 없는 학생은 제외하고, 성적이 있는 학생들만 총점 순으로 정렬
            sql = """
                SELECT m.name, m.uid, s.* FROM scores s
                JOIN members m ON s.member_id = m.id
                ORDER BY s.total DESC
            """
            cursor.execute(sql)
            datas = cursor.fetchall()
            print(f"sql 결과 테스트 : {datas}")

            # 3. DB에서 가져온 딕셔너리 리스트를 Score 객체 리스트로 변환
            score_objects = []
            for data in datas:
                # Score 클래스에 정의하신 from_db 활용
                s = Score.from_db(data) # 직렬화 (dict 타입 -> 객체)
                # 객체에 있는 이름(name) 정보는 수동으로 살짝 넣어주기 (join에서 만든 값 사용)
                s.name = data['name']
                s.uid = data['uid']
                score_objects.append(s)

            return render_template('score_list.html', scores=score_objects)
            #                       프론트화면 ui에                      성적이 담긴 리스트 객체를 전달
    finally:
        conn.close()

@app.route('/score/members')
def score_members():
    if session.get('user_role') not in ('admin','manager'):
        return "<script>alert('권한이 없습니다.');history.back()</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # LEFT JOIN을 통해 성적이 있으면 s.id가 숫자로, 없으면 NULL로 나옴
            sql = """
                SELECT m.id, m.uid, m.name, s.id AS score_id
                FROM members m
                LEFT JOIN scores s ON m.id = s.member_id
                WHERE m.role = 'user'
                ORDER BY m.name ASC
            """
            cursor.execute(sql)
            members = cursor.fetchall()
            return render_template('score_member_list.html', members=members)
    finally:
        conn.close()

@app.route('/score/my') # http://localhost:5000/score/my -> GET방식
def score_my():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 내 ID로만 조회
            sql = "SELECT * FROM scores WHERE member_id = %s;"
            cursor.execute(sql, (session['user_id'],))
            row = cursor.fetchone()
            print(row)

            # Score 객체로 변환 (from_db 활용)
            score = Score.from_db(row) if row else None

            return render_template('score_my.html', score=score)
    finally:
        conn.close()

######################################### 성적 CRUD END ################################################################

######################################### 파일 게시판 CRUD ##############################################################

# 파일처리용 게시판 특징
# 1. 파일 업로드/다운로드 가능
# 2. 단일파일/다중파일 업로드 처리
# 3. 서비스 패키지 활용
## 4. /upload 폴더 사용 / 용량 제한 16MB
# 5. 파일명 중복 방지용 코드 활용
# 6. db에서 부모 객체가 삭제되면 자식 객체도 삭제되게 cascade 처리

UPLOAD_FOLDER = './uploads'
# 폴더가 없으면 자동 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    # 폴더 생성용 코드 os.makedirs(이름)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# 최대 업로드 용량 제한 (예 : 16MB)
# bit -> 0, 1
# 1 byte -> 8 bit -> 0~255 (256개의 값을 가짐)
# 1 KB -> 1024 byte
# 1 MB -> 1024 KB
# 1 GB -> 1024 MB
# 1 TB -> 1024 GB
# 1 PB -> 1024 TB
# 1 XB -> 1024 PB

@app.route('/filesboard/write', methods=['GET','POST'])
def filesboard_write():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        # 핵심 : getlist를 사용해야 리스트 형태로 가져옴
        files = request.files.getlist('files')
        # 파일 처리 시 html 필수 코드 : enctype = 'multipart/form-data'

        if PostService.save_post(session['user_id'], title, content, files):
            return "<script>alert('게시글이 등록되었습니다.');location.href='/filesboard';</script>"
        else:
            return "<script>alert('등록실패');history.back()</script>"

    return render_template('filesboard_write.html')

# 파일 게시판 목록
@app.route('/filesboard')
def filesboard_list():
    posts = PostService.get_posts()
    return render_template('filesboard_list.html', posts=posts)

# 파일 게시판 상세 보기
@app.route('/filesboard/view/<int:post_id>')
def filesboard_view(post_id):
    post, files = PostService.get_post_detail(post_id) # 두개를 리턴하면 두개로 받아야함
    if not post:
        return "<script>alert('해당 게시글이 없습니다.'); location.href='/filesboard';</script>"
    return render_template('filesboard_view.html', post=post, files=files)

# send_from_directory 사용하여 자료 다운로드 가능
@app.route('/download/<path:filename>')
def download_file(filename):
    # 파일이 저장된 폴더(uploads)에서 파일을 찾아 전송합니다.
    # 프론트 <a href="{{ url_for('download_file', filename=file.save_name) }}" ...> 이부분 처리용
    # filename은 서버에 저장된 save_name입니다.
    # 브라우저가 다운로드할 때 보여줄 원본 이름을 쿼리 스트링으로 받거나 DB에서 가져와야 합니다.
    origin_name = request.args.get('origin_name')
    return send_from_directory('uploads/', filename, as_attachment=True, download_name=origin_name)
    # from flask import send_from_directory 필수

    #   return send_from_directory('uploads/', filename)는 브라우져에서 바로 열어버림
    #   as_attachment=True 로 하면 파일 다운로드 창을 띄움
    #   저장할 파일명은 download_name=origin_name 로 지정

@app.route('/filesboard/delete/<int:post_id>')
def filesboard_delete(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 삭제 전 작성자 확인을 위해 정보 조회
    post, _ = PostService.get_post_detail(post_id)
    # _은 리턴값을 사용하지 않겠다 라는 관례적인 표현 (_) 사용하지 않는 변수

    if not post:
        return "<script>alert('이미 삭제된 게시글입니다.'); location.href='/filesboard';</script>"

    # 본인 확인 (또는 관리자 권한)
    if post['member_id'] != session['user_id'] and session.get('user_role') != 'admin':
        return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"

    if PostService.delete_post(post_id):
        return "<script>alert('성공적으로 삭제되었습니다.'); location.href='/filesboard';</script>"
    else:
        return "<script>alert('삭제 중 오류가 발생했습니다.'); history.back();</script>"


# 다중파일 수정용
@app.route('/filesboard/edit/<int:post_id>', methods=['GET', 'POST'])
def filesboard_edit(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files')  # 다중 파일 가져오기

        if PostService.update_post(post_id, title, content, files):
            return f"<script>alert('수정되었습니다.'); location.href='/filesboard/view/{post_id}';</script>"
        return "<script>alert('수정 실패'); history.back();</script>"

    # GET 요청 시 기존 데이터 로드
    post, files = PostService.get_post_detail(post_id)
    if post['member_id'] != session['user_id']:
        return "<script>alert('권한이 없습니다.'); history.back();</script>"

    return render_template('filesboard_edit.html', post=post, files=files)









######################################### 파일 게시판 CRUD ##############################################################
@app.route('/')
def index():
    return render_template("main.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)