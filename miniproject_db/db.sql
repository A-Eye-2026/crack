CREATE DATABASE lms DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE LMS; # LMS 데이터베이스를 사용
CREATE TABLE members ( # members 테이블 생성
# 필드명 타입 옵션
   id  INT AUTO_INCREMENT PRIMARY KEY, 
#      정수 자동번호생성기      기본키 (다른테이블과 연결용)
  uid VARCHAR(50) NOT NULL UNIQUE,
#   가변문자(50자) 공백 비허용 유일한값
password VARCHAR(255) NOT NULL,
name VARCHAR(50) NOT NULL,
role ENUM('admin','manager','user') DEFAULT 'user',
#    열거타입(관호안에 글자만 허용)         기본값 = user
active BOOLEAN DEFAULT TRUE,
#      불린타입       기본값     TRUE = 1, FALSE = 0으로 저장
created_at DATETIME DEFAULT CURRENT_TIMESTAMP
# 생성일     날짜시간타입     기본값 = 시스템시간
);

SELECT * FROM members;

INSERT INTO members (uid, password, name, role, active) VALUES
('admin01', 'admin123', '김관리', 'admin', TRUE),
('manager01', 'manager123', '박매니저', 'manager', TRUE),
('user01', 'user123', '이민수', 'user', TRUE),
('user02', 'user123', '최지훈', 'user', TRUE),
('user03', 'user123', '정다은', 'user', TRUE),
('user04', 'user123', '한지민', 'user', TRUE),
('user05', 'user123', '강수현', 'user', TRUE),
('user06', 'user123', '윤서준', 'user', FALSE),
('user07', 'user123', '장하늘', 'user', TRUE),
('user08', 'user123', '오세훈', 'user', TRUE);

# 더미데이터 입력
INSERT INTO members(uid,password,name,role,active)
VALUES('kkw','1234','김기원','admin',TRUE),
('lhj','1234','임효정','manager',TRUE),
('ljj','1234','이재정','user',TRUE),
('ljk','1234','이지건','user',TRUE),
('kdg','1234','김도균','user',TRUE);

CREATE TABLE incidents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NULL,
    title VARCHAR(200) NOT NULL,
    location VARCHAR(255) NOT NULL,
    region_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    image_path VARCHAR(255),
    status VARCHAR(50) DEFAULT '접수완료',
    risk_score DECIMAL(5,2) DEFAULT 0,
    first_created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_checked_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id)
);

INSERT INTO incidents
(member_id, title, location, region_name, latitude, longitude, image_path, status, risk_score)
VALUES
(13, '도로 균열 발생', '화성시 봉정동', '경기도', 37.2072000, 127.0330000, NULL, '접수완료', 85),
(11, '보도블럭 파손', '안양시 동안구 호계동', '경기도', 37.3943000, 126.9568000, NULL, '접수완료', 62),
(5, '도로 함몰 위험', '군포시 산본동', '경기도', 37.3616000, 126.9352000, NULL, '접수완료', 55),
(7, '포트홀 신고', '오산시 원동', '경기도', 37.1498000, 127.0772000, NULL, '접수완료', 40);

select * from incidents;

CREATE TABLE incident_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    incident_id INT NOT NULL,
    member_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    image_path VARCHAR(255),
    risk_score DECIMAL(5,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(id),
    FOREIGN KEY (member_id) REFERENCES members(id)
);

ALTER TABLE incident_reports
ADD CONSTRAINT uq_incident_member UNIQUE (incident_id, member_id);

INSERT INTO incident_reports
(incident_id, member_id, title, location, latitude, longitude, image_path, risk_score)
VALUES
(2, 13, '보도블럭 파손', '안양시 동안구 호계동', 37.3943000, 126.9568000, NULL, 62),
(2, 11, '보도블럭 파손', '안양시 동안구 호계동', 37.3943100, 126.9568100, NULL, 61),
(2, 5,  '보도블럭 파손', '안양시 동안구 호계동', 37.3943200, 126.9568200, NULL, 63);

select * from incident_reports;

UPDATE incidents
SET image_path = 'test1.jpg'
WHERE id = 1;

ALTER TABLE incidents ADD video_path VARCHAR(255) NULL;
ALTER TABLE incident_reports ADD video_path VARCHAR(255) NULL;

SELECT id, title, image_path FROM incidents WHERE id = 1;