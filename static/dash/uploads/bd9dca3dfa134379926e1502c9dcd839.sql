-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 192.168.0.150    Database: lms
-- ------------------------------------------------------
-- Server version	8.4.8

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `posts`
--

DROP TABLE IF EXISTS `posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `member_id` int NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_general_ci NOT NULL,
  `content` text COLLATE utf8mb4_general_ci NOT NULL,
  `view_count` int DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `member_id` (`member_id`),
  CONSTRAINT `posts_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `members` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `posts`
--

LOCK TABLES `posts` WRITE;
/*!40000 ALTER TABLE `posts` DISABLE KEYS */;
INSERT INTO `posts` VALUES (3,2,'다중파일 업로드 테스트','3개 넣어 보장~',17,'2026-02-03 15:15:49','2026-02-03 15:26:15'),(4,2,'pdf 업로드 테스트','pdf도 테스트 해보자!',20,'2026-02-03 15:17:25','2026-02-04 15:09:22'),(5,14,'귀여움 (수정)','강아지 최고\r\n고양이도 최고',15,'2026-02-03 15:20:01','2026-02-04 15:09:24'),(6,12,'파이썬 21일차 공부내용','파이썬 공부내용',6,'2026-02-03 15:20:04','2026-02-03 15:23:40'),(7,23,'안녕(수정)','귀욤댕이 강쥐보세여~~~\r\n안넝',13,'2026-02-03 15:20:23','2026-02-03 15:24:54'),(8,24,'로그인 화면 이미지 파일<뚜정>','예뿌당 호호호호',16,'2026-02-03 15:20:29','2026-02-03 15:24:41'),(9,13,'괭','고양이',7,'2026-02-03 15:20:32','2026-02-03 15:22:38'),(10,21,'자료등록화면','자료등록화면',11,'2026-02-03 15:20:34','2026-02-04 15:09:20'),(11,3,'HTML공부','HTML공부',8,'2026-02-03 15:20:55','2026-02-04 15:09:26'),(12,27,'크리스탈','펭귄아님 이었음',16,'2026-02-03 15:21:01','2026-02-03 15:25:17'),(13,26,'자료등록 테스트','테스트',9,'2026-02-03 15:21:28','2026-02-03 15:24:37'),(14,3,'HTML','26.02.03 연습',16,'2026-02-03 15:22:19','2026-02-03 15:25:12'),(15,19,'.','너구리',5,'2026-02-03 15:22:23','2026-02-04 15:09:39'),(16,18,'HTML','\r\n태그(Tag): 브라우저에게 \"이 데이터는 무엇이다\"라고 알려주는 명령어입니다.\r\n\r\n시맨틱(Semantic): 의미가 명확한 태그(<nav>, <article>)를 쓰는 것이 좋은 코드입니다.\r\n\r\n속성(Attribute): 태그 옆에 붙는 설정값(<a href=\"...\">)으로 기능을 확장합니다.\r\n1. 구조 설계 (Layout)\r\n웹페이지의 구역을 나누는 큰 틀입니다.\r\n<header> : 페이지 최상단 (로고, 메인 메뉴 구역)\r\n<nav>    : 내비게이션 (메뉴, 링크 모음 구역)\r\n<main>   : 페이지의 핵심 본문 내용 (페이지당 한 번만 사용)\r\n<section>: 본문 내의 큰 주제별 구역\r\n<article>: 독립적인 콘텐츠 (블로그 글, 뉴스 기사)\r\n<aside>  : 사이드바 (본문 옆의 부가 정보)\r\n<footer> : 페이지 최하단 (저작권, 주소, 연락처)\r\n<div>    : 아무 의미 없는 범용 박스 (단순히 묶을 때 사용)\r\n\r\n2. 텍스트 표현 (Text)\r\n화면에 글자를 출력하고 강조하는 요소입니다.\r\n    <h1>~<h6>: 제목 (숫자가 작을수록 크고 중요한 제목)\r\n<p>      : 문단 (일반적인 텍스트 덩어리)\r\n<span>   : 문장 내 특정 부분만 감싸는 용도 (디자인용)\r\n<a>      : 하이퍼링크 (클릭 시 페이지 이동)\r\n<strong> : 글자 굵게 강조 (중요한 내용)\r\n<em>     : 글자 기울임 강조 (강조하고 싶은 내용)\r\n<br>     : 강제 줄바꿈 (닫는 태그 없음)\r\n<hr>     : 수평 구분선 (닫는 태그 없음)\r\n\r\n 3. 목록 생성 (List)\r\n 데이터를 나열할 때 사용하는 자료구조형 태그입니다.\r\n<ul> : 순서가 없는 목록 (불렛 포인트)\r\n<ol> : 순서가 있는 목록 (1, 2, 3 번호)\r\n<li> : 목록 내부의 각 개별 항목\r\n\r\n 4. 사용자 입력 (Forms)\r\n사용자의 데이터를 받는 인터페이스입니다.\r\n<form>    : 입력된 데이터를 서버로 전달하는 전체 묶음\r\n<input>   : 글자 입력, 체크박스 등 다양한 입력창 (닫는 태그 없음)\r\n<label>   : 입력창(input)에 붙이는 이름표\r\n<textarea>: 여러 줄을 입력할 수 있는 넓은 입력창\r\n<select>  : 드롭다운 선택 목록\r\n<button>  : 클릭 가능한 실행 버튼\r\n\r\n 5. 미디어 및 표 (Media & Table)\r\n시각적인 정보나 표 형식을 나타냅니다.\r\n<img>  : 이미지 출력 (닫는 태그 없음)\r\n<table>: 표 전체 틀\r\n<tr>   : 표의 한 행 (가로줄)\r\n<th>   : 표의 제목 칸 (굵게 표시됨)\r\n<td>   : 표의 일반 데이터 칸\r\n-->',11,'2026-02-03 15:24:12','2026-02-04 15:09:31'),(18,11,'다중파일 수정','다중파일 수정',7,'2026-02-03 15:33:18','2026-02-04 15:09:29');
/*!40000 ALTER TABLE `posts` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-12  9:52:29
