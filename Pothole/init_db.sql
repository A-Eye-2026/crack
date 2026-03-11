-- =====================================================
-- Aeye 프로젝트 로컬 MySQL 초기화 스크립트
-- 실행: mysql -u root -p < init_db.sql
-- =====================================================

CREATE DATABASE IF NOT EXISTS aeye_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE aeye_db;

-- ─────────────────────────────────────────────
-- 1. 회원 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS members (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    uid          VARCHAR(100)  NOT NULL UNIQUE,
    password     VARCHAR(255)  NOT NULL,
    name         VARCHAR(100)  NOT NULL,
    email        VARCHAR(200)  DEFAULT NULL,
    role         VARCHAR(20)   NOT NULL DEFAULT 'user',
    active       TINYINT(1)    NOT NULL DEFAULT 1,
    profile_photo VARCHAR(500) DEFAULT NULL,
    cover_photo  VARCHAR(500)  DEFAULT NULL,
    quiz_progress TEXT         DEFAULT NULL,
    last_active  DATETIME      DEFAULT NULL,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 2. 게시판 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS boards (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    member_id  INT           NOT NULL,
    title      VARCHAR(255)  NOT NULL,
    content    TEXT,
    image_url  VARCHAR(500)  DEFAULT NULL,
    views      INT           NOT NULL DEFAULT 0,
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 3. 자료실(posts) 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posts (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    member_id  INT           NOT NULL,
    title      VARCHAR(255)  NOT NULL,
    content    TEXT,
    image_url  VARCHAR(500)  DEFAULT NULL,
    views      INT           NOT NULL DEFAULT 0,
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 4. 좋아요 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS likes (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT          NOT NULL,
    post_id   INT          NOT NULL,
    post_type VARCHAR(20)  NOT NULL DEFAULT 'board',
    created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_like (member_id, post_id, post_type),
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 5. 성적 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scores (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    member_id  INT          NOT NULL,
    subject    VARCHAR(100) NOT NULL,
    score      INT          NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 6. 상품 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255)   NOT NULL,
    description TEXT,
    price       INT            NOT NULL DEFAULT 0,
    image_url   VARCHAR(500)   DEFAULT NULL,
    created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 7. 주문(장바구니) 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    member_id  INT  NOT NULL,
    product_id INT  NOT NULL,
    quantity   INT  NOT NULL DEFAULT 1,
    is_hidden  TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id)  REFERENCES members(id)  ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 8. AI 이미지 탐지 게시글 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_detect_posts (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    member_id     INT          DEFAULT NULL,
    title         VARCHAR(255) NOT NULL,
    content       TEXT,
    image_path    VARCHAR(500) DEFAULT NULL,
    detect_result TEXT         DEFAULT NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 9. AI 영상 탐지 게시글 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_video_posts (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    member_id         INT          DEFAULT NULL,
    title             VARCHAR(255) NOT NULL,
    content           TEXT,
    origin_video_path VARCHAR(500) DEFAULT NULL,
    result_video_path VARCHAR(500) DEFAULT NULL,
    status            VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    total_frames      INT          NOT NULL DEFAULT 0,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 10. AI 영상 프레임 상세 탐지 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_video_details (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    video_post_id    INT  NOT NULL,
    frame_number     INT  NOT NULL DEFAULT 0,
    detected_objects JSON DEFAULT NULL,
    FOREIGN KEY (video_post_id) REFERENCES ai_video_posts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 11. 사이트 방문 통계 테이블
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS site_stats (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    total_visits  INT  NOT NULL DEFAULT 0,
    today_visits  INT  NOT NULL DEFAULT 0,
    last_date     DATE DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 기본 데이터: site_stats 초기 행 삽입
INSERT INTO site_stats (id, total_visits, today_visits, last_date)
VALUES (1, 0, 0, CURDATE())
ON DUPLICATE KEY UPDATE id = id;

-- ─────────────────────────────────────────────
-- 12. 조회수 추적 테이블 (view_logs)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS view_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,
    item_id INT NULL,
    member_id VARCHAR(50) NULL,
    ip_address VARCHAR(64) NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item (item_type, item_id),
    INDEX idx_ip_time (ip_address, viewed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────
-- 완료 메시지
-- ─────────────────────────────────────────────
SELECT 'Aeye DB 초기화 완료!' AS result;
SHOW TABLES;
