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
-- Table structure for table `members`
--

DROP TABLE IF EXISTS `members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uid` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `role` enum('admin','manager','user') COLLATE utf8mb4_general_ci DEFAULT 'user',
  `active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uid` (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `members`
--

LOCK TABLES `members` WRITE;
/*!40000 ALTER TABLE `members` DISABLE KEYS */;
INSERT INTO `members` VALUES (2,'kkw','8188','김기원','admin',1,'2026-01-28 12:12:03'),(3,'lhj','1021','임효정','manager',1,'2026-01-28 12:12:03'),(4,'kdg','1111','김도균','user',1,'2026-01-28 12:12:03'),(5,'ksb','7410','김수빈','user',1,'2026-01-28 12:12:03'),(6,'kjy','3333','김지영','manager',1,'2026-01-28 12:12:03'),(7,'kkk','kkk','kkk','admin',1,'2026-01-28 16:38:24'),(8,'jjj','jjj','jjj','user',1,'2026-01-30 13:07:40'),(10,'aaa','aaa','aaa','user',1,'2026-02-02 11:39:07'),(11,'test','test','test','admin',1,'2026-02-02 15:19:06'),(12,'psh','1234','박승호','user',1,'2026-02-02 15:21:11'),(13,'syk','0801','심유경','user',1,'2026-02-02 15:21:23'),(14,'아구몬','1234','아구몬','user',1,'2026-02-02 15:21:28'),(15,'ejj','1111','은재','user',1,'2026-02-02 15:21:41'),(16,'kkw1','1234','kkw','user',1,'2026-02-02 15:21:47'),(17,'www','1234','월드','user',1,'2026-02-02 15:21:51'),(18,'bob','111','bob','user',1,'2026-02-02 15:21:53'),(19,'elex3245','1234','김사브리나','user',1,'2026-02-02 15:21:54'),(20,'yjs','1111','유진설','user',1,'2026-02-02 15:21:55'),(21,'ji0','1234','김지영','user',1,'2026-02-02 15:21:56'),(22,'ymy','0807','인계동불빠따','user',1,'2026-02-02 15:23:10'),(23,'apfhd','8888','안알랴줌','user',1,'2026-02-02 15:23:10'),(24,'kdh','1234','김도하','user',1,'2026-02-02 16:54:54'),(25,'zzz','zzz','zzz','user',1,'2026-02-03 15:19:16'),(26,'KKB','1111','김개발','user',1,'2026-02-03 15:19:21'),(27,'kkw2','1234','kkw2','user',1,'2026-02-03 15:19:24'),(28,'안녕하세요','1111','DDD','user',1,'2026-02-03 15:21:37'),(29,'mbc','mbc','엠비씨','user',1,'2026-02-09 09:56:00'),(30,'susan','susan','조정화 ','user',1,'2026-02-09 10:09:30'),(31,'rhl','1111','노형래','user',1,'2026-02-09 10:09:47'),(32,'song','song','송','user',1,'2026-02-09 10:09:50'),(33,'mbc1','mbc1','mbc1','user',1,'2026-02-09 10:09:54'),(34,'pat','1111','패트','user',1,'2026-02-09 12:48:42'),(35,'hhu','0000','홍현우','user',1,'2026-02-09 12:49:15'),(36,'kdg7777','ehrbs','김도균','user',1,'2026-02-09 12:52:38'),(37,'khj','khj','김효진','user',1,'2026-02-09 12:52:44'),(38,'elex4236','12345','김사브리나2','user',1,'2026-02-09 12:52:49'),(39,'이지건','1234','이지건','user',1,'2026-02-09 12:52:49'),(40,'abc','1234','파이리','user',1,'2026-02-09 12:52:54'),(41,'ppsh','1234','박승호','user',1,'2026-02-09 12:52:55'),(42,'coffee','1111','스페셜티','user',1,'2026-02-09 12:52:57'),(43,'kss','2222','김수빈','user',1,'2026-02-09 12:53:04'),(44,'ddd','0000','김동동','user',1,'2026-02-09 12:53:05'),(45,'uuu','kkk','유유유','user',1,'2026-02-09 12:53:08'),(46,'yjs123','1111','유진설','user',1,'2026-02-09 12:53:10'),(47,'qwer','1234','큐다블알','user',1,'2026-02-09 12:53:34'),(48,'kdg3351','ehrbs','김도균','user',1,'2026-02-09 12:54:43'),(49,'rho','1111','노형래','user',1,'2026-02-09 12:54:45'),(50,'zzzz','1234','아무개','user',1,'2026-02-09 12:54:45'),(51,'lee','1234','이지건','user',1,'2026-02-09 12:55:20'),(52,'kdk5512','ehrbs','kdk','user',1,'2026-02-09 12:55:35'),(53,'ccc','0000','박동동','user',1,'2026-02-09 12:55:44'),(54,'bbaengggu','0801','ㅍvㅍ','user',1,'2026-02-09 12:55:47'),(55,'wow','1234','치와와','user',1,'2026-02-09 12:55:52'),(56,'www00','0000','이동동','user',1,'2026-02-09 12:57:41'),(57,'FPP','4321','김드론','user',1,'2026-02-09 14:42:20'),(58,'test1','1234','테스트1','user',1,'2026-02-09 18:28:10'),(59,'ksh','1102','๑◉ Å ◉๑','user',1,'2026-02-10 10:39:41'),(60,'elex42362','1234','123','user',1,'2026-02-10 15:28:48'),(61,'elex4236234','1234','1234','user',1,'2026-02-10 15:31:15'),(62,'kkww','kkww','kkww','user',1,'2026-02-11 09:51:38'),(63,'lhj2','1021','임효정','user',1,'2026-02-11 09:51:38'),(64,'bbb','bbb','점수없음','user',1,'2026-02-11 12:08:26');
/*!40000 ALTER TABLE `members` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-12  9:52:28
