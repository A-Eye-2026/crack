CREATE DATABASE lms DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE LMS; # LMS 데이터베이스를 사용
CREATE TABLE members (
   id INT AUTO_INCREMENT PRIMARY KEY,
   uid VARCHAR(50) NOT NULL UNIQUE,
   password VARCHAR(255) NOT NULL,
   name VARCHAR(50) NOT NULL,
   role ENUM('admin','manager','user') DEFAULT 'user',
   active BOOLEAN DEFAULT TRUE,
   manager_region VARCHAR(100) NULL,
   created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO members (uid, password, name, role, active, manager_region) VALUES
('admin01',   '1234', '총관리자',     'admin',   TRUE,  NULL),
('manager01', '1234', '분당구담당자', 'manager', TRUE,  '성남시 분당구'),
('manager02', '1234', '수정구담당자', 'manager', TRUE,  '성남시 수정구'),
('manager03', '1234', '영통구담당자', 'manager', TRUE,  '수원시 영통구'),
('manager04', '1234', '장안구담당자', 'manager', TRUE,  '수원시 장안구'),
('user01',    '1234', '김민수',       'user',    TRUE,  NULL),
('user02',    '1234', '이서연',       'user',    TRUE,  NULL),
('user03',    '1234', '박지훈',       'user',    TRUE,  NULL),
('user04',    '1234', '최유진',       'user',    TRUE,  NULL),
('user05',    '1234', '정하늘',       'user',    TRUE,  NULL);

INSERT INTO members (uid, password, name, role, active, manager_region) VALUES
('manager05', '1234', '권선구담당자', 'manager', TRUE, '수원시 권선구'),
('manager06', '1234', '동안구담당자', 'manager', TRUE, '안양시 동안구'),
('user11', '1234', '노지훈', 'user', TRUE, NULL),
('user12', '1234', '백서윤', 'user', TRUE, NULL),
('user13', '1234', '임도윤', 'user', TRUE, NULL),
('user14', '1234', '서지안', 'user', TRUE, NULL),
('user15', '1234', '한도경', 'user', TRUE, NULL);

SELECT * FROM members;

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

ALTER TABLE incidents
MODIFY COLUMN status ENUM('접수완료','처리중','처리완료','반려') DEFAULT '접수완료';

INSERT INTO incidents
(member_id, title, location, region_name, latitude, longitude, image_path, status, risk_score, first_created_at)
VALUES
(11, '정자동 추가 포트홀', '성남시 분당구 정자동 20-1', '성남시 분당구', 37.3595600, 127.1053800, 'pothole_101.jpg', '접수완료', 91.00, '2026-03-18 14:00:00'),
(12, '정자동 도로 손상',   '성남시 분당구 정자동 20-3', '성남시 분당구', 37.3595700, 127.1054000, 'pothole_102.jpg', '접수완료', 89.00, '2026-03-18 14:10:00'),
(13, '정자동 파손 심각',   '성남시 분당구 정자동 20-5', '성남시 분당구', 37.3595800, 127.1054100, 'pothole_103.jpg', '처리중',   95.00, '2026-03-18 14:20:00');

INSERT INTO incidents VALUES
(NULL, 14, '야탑동 미세 균열', '성남시 분당구 야탑동 200', '성남시 분당구', 37.4100000, 127.1250000, 'pothole_104.jpg', '접수완료', 20.00, '2026-03-18 13:00:00', NOW()),
(NULL, 15, '서현동 작은 파임', '성남시 분당구 서현동 150', '성남시 분당구', 37.3850000, 127.1220000, 'pothole_105.jpg', '접수완료', 30.00, '2026-03-18 12:30:00', NOW());

INSERT INTO incidents VALUES
(NULL, 11, '허위 신고 테스트', '성남시 수정구 태평동 999', '성남시 수정구', 37.4410000, 127.1370000, 'pothole_106.jpg', '반려', 50.00, '2026-03-17 11:00:00', NOW());

INSERT INTO incidents
(member_id, title, location, region_name, latitude, longitude, image_path, status, risk_score, first_created_at)
VALUES
(12, '영통 중심 도로 파손', '수원시 영통구 영통동 200', '수원시 영통구', 37.2515000, 127.0713000, 'pothole_107.jpg', '접수완료', 85.00, '2026-03-18 15:00:00'),
(13, '망포역 인근 균열',   '수원시 영통구 망포동 400', '수원시 영통구', 37.2460000, 127.0565000, 'pothole_108.jpg', '처리중',   82.00, '2026-03-18 15:10:00'),
(14, '광교 도로 손상',     '수원시 영통구 이의동 1200', '수원시 영통구', 37.2862000, 127.0520000, 'pothole_109.jpg', '접수완료', 88.00, '2026-03-18 15:20:00'),
(15, '광교 미세 파손',     '수원시 영통구 이의동 1205', '수원시 영통구', 37.2863000, 127.0521000, 'pothole_110.jpg', '접수완료', 25.00, '2026-03-18 15:30:00');

INSERT INTO incidents VALUES
(NULL, 11, '강남 포트홀', '서울시 강남구 역삼동 800', '서울시 강남구', 37.4978000, 127.0275000, 'pothole_111.jpg', '접수완료', 93.00, '2026-03-18 10:00:00', NOW()),
(NULL, 12, '잠실 도로 균열', '서울시 송파구 잠실동 50', '서울시 송파구', 37.5110000, 127.0980000, 'pothole_112.jpg', '처리중', 87.00, '2026-03-18 09:00:00', NOW());

INSERT INTO incidents
(member_id, title, location, region_name, latitude, longitude, image_path, status, risk_score, first_created_at)
VALUES
-- 성남시 분당구 / 비슷한 위치 묶음 테스트
(6, '정자동 포트홀 신고', '성남시 분당구 정자동 15-3', '성남시 분당구', 37.3595700, 127.1053990, 'pothole_001.jpg', '접수완료', 92.50, '2026-03-18 08:10:00'),
(7, '정자동 도로 균열',   '성남시 분당구 정자동 15-5', '성남시 분당구', 37.3596100, 127.1054200, 'pothole_002.jpg', '접수완료', 88.00, '2026-03-18 09:00:00'),
(8, '정자동 파손 신고',   '성남시 분당구 정자동 16-1', '성남시 분당구', 37.3595400, 127.1053600, 'pothole_003.jpg', '처리중',   84.30, '2026-03-18 10:10:00'),

-- 성남시 분당구 / 따로 떨어진 건
(9,  '서현역 인근 포트홀', '성남시 분당구 서현동 245-4', '성남시 분당구', 37.3852200, 127.1231000, 'pothole_004.jpg', '처리중',   76.20, '2026-03-18 07:40:00'),
(10, '야탑동 도로 파임',   '성남시 분당구 야탑동 367-2', '성남시 분당구', 37.4111000, 127.1285000, 'pothole_005.jpg', '처리완료', 65.00, '2026-03-17 15:20:00'),

-- 성남시 수정구
(6,  '태평동 포트홀',      '성남시 수정구 태평동 7288', '성남시 수정구', 37.4410200, 127.1379000, 'pothole_006.jpg', '접수완료', 81.00, '2026-03-18 06:55:00'),
(7,  '신흥동 도로 균열',   '성남시 수정구 신흥동 4123', '성남시 수정구', 37.4408500, 127.1472000, 'pothole_007.jpg', '반려',     40.00, '2026-03-17 12:00:00'),
(8,  '복정동 침하 의심',   '성남시 수정구 복정동 689',  '성남시 수정구', 37.4705000, 127.1267000, 'pothole_008.jpg', '처리중',   78.00, '2026-03-18 11:40:00'),

-- 성남시 중원구
(9,  '상대원동 포트홀',    '성남시 중원구 상대원동 145', '성남시 중원구', 37.4381000, 127.1653000, 'pothole_009.jpg', '접수완료', 55.00, '2026-03-18 08:45:00'),
(10, '은행동 도로 손상',   '성남시 중원구 은행동 1024', '성남시 중원구', 37.4554000, 127.1681000, 'pothole_010.jpg', '처리완료', 82.00, '2026-03-17 17:30:00'),

-- 수원시 영통구 / 비슷한 위치 묶음 테스트
(6,  '영통역 앞 포트홀',   '수원시 영통구 영통동 998-5', '수원시 영통구', 37.2514000, 127.0712000, 'pothole_011.jpg', '접수완료', 90.00, '2026-03-18 08:00:00'),
(7,  '영통동 파손 도로',   '수원시 영통구 영통동 998-7', '수원시 영통구', 37.2514300, 127.0712400, 'pothole_012.jpg', '접수완료', 87.00, '2026-03-18 08:20:00'),
(8,  '영통동 함몰 신고',   '수원시 영통구 영통동 999-1', '수원시 영통구', 37.2513900, 127.0711800, 'pothole_013.jpg', '처리중',   93.00, '2026-03-18 09:10:00'),

-- 수원시 영통구 / 별도 건
(9,  '망포동 균열',        '수원시 영통구 망포동 322-14', '수원시 영통구', 37.2459000, 127.0563000, 'pothole_014.jpg', '처리완료', 72.00, '2026-03-17 10:20:00'),
(10, '광교중앙로 파손',    '수원시 영통구 이의동 1332',   '수원시 영통구', 37.2863000, 127.0518000, 'pothole_015.jpg', '접수완료', 79.50, '2026-03-18 12:05:00'),

-- 수원시 장안구
(6,  '조원동 포트홀',      '수원시 장안구 조원동 752', '수원시 장안구', 37.3015000, 127.0102000, 'pothole_016.jpg', '접수완료', 83.40, '2026-03-18 07:15:00'),
(7,  '정자동 도로 갈라짐', '수원시 장안구 정자동 36-12', '수원시 장안구', 37.3057000, 126.9991000, 'pothole_017.jpg', '반려',     35.00, '2026-03-17 16:40:00'),
(8,  '율전동 요철 심함',   '수원시 장안구 율전동 101-7', '수원시 장안구', 37.2992000, 126.9708000, 'pothole_018.jpg', '처리중',   86.00, '2026-03-18 13:20:00'),

-- 수원시 권선구
(9,  '권선동 포장 파손',   '수원시 권선구 권선동 1020', '수원시 권선구', 37.2572000, 127.0311000, 'pothole_019.jpg', '처리완료', 68.00, '2026-03-17 09:00:00'),
(10, '세류동 침하',        '수원시 권선구 세류동 1105', '수원시 권선구', 37.2526000, 127.0135000, 'pothole_020.jpg', '접수완료', 88.80, '2026-03-18 14:10:00'),

-- 수원시 팔달구
(6,  '인계동 도로 파임',   '수원시 팔달구 인계동 1121-3', '수원시 팔달구', 37.2658000, 127.0289000, 'pothole_021.jpg', '처리중',   80.00, '2026-03-18 11:05:00'),
(7,  '우만동 파손 신고',   '수원시 팔달구 우만동 92-5',   '수원시 팔달구', 37.2840000, 127.0337000, 'pothole_022.jpg', '접수완료', 74.00, '2026-03-18 15:15:00'),

-- 서울시 강남구
(8,  '역삼동 포트홀',      '서울시 강남구 역삼동 820-9', '서울시 강남구', 37.4979000, 127.0276000, 'pothole_023.jpg', '접수완료', 91.00, '2026-03-18 08:35:00'),
(9,  '삼성동 도로 균열',   '서울시 강남구 삼성동 159',   '서울시 강남구', 37.5146000, 127.0635000, 'pothole_024.jpg', '처리완료', 62.00, '2026-03-17 18:50:00'),

-- 서울시 송파구
(10, '잠실동 함몰 의심',   '서울시 송파구 잠실동 40-1', '서울시 송파구', 37.5111000, 127.0982000, 'pothole_025.jpg', '처리중',   89.20, '2026-03-18 09:55:00'),

-- 안양시 동안구
(6,  '평촌동 포트홀',      '안양시 동안구 평촌동 899', '안양시 동안구', 37.3946000, 126.9568000, 'pothole_026.jpg', '접수완료', 77.00, '2026-03-18 10:45:00'),

-- 용인시 수지구
(7,  '죽전동 도로 손상',   '용인시 수지구 죽전동 1288', '용인시 수지구', 37.3242000, 127.1089000, 'pothole_027.jpg', '반려',     42.00, '2026-03-17 13:35:00');

INSERT INTO incidents
(member_id, title, location, region_name, latitude, longitude, image_path, status, risk_score, first_created_at)
VALUES
(6, '야탑역 근처 작은 파손', '성남시 분당구 야탑동 123-1', '성남시 분당구', 37.4110000, 127.1280000, 'pothole_dup_001.jpg', '접수완료', 22.00, '2026-03-18 10:00:00'),
(7, '야탑역 도로 미세 균열', '성남시 분당구 야탑동 123-2', '성남시 분당구', 37.4110200, 127.1280100, 'pothole_dup_002.jpg', '접수완료', 28.00, '2026-03-18 11:00:00'),
(8, '야탑동 동일 구간 재신고', '성남시 분당구 야탑동 123-3', '성남시 분당구', 37.4110100, 127.1280200, 'pothole_dup_003.jpg', '접수완료', 25.00, '2026-03-18 12:00:00');

select * from incidents;

UPDATE incidents
SET image_path = 'test1.jpg'
WHERE id = 1;

ALTER TABLE incidents ADD video_path VARCHAR(255) NULL;

SELECT id, title, image_path FROM incidents WHERE id = 1;