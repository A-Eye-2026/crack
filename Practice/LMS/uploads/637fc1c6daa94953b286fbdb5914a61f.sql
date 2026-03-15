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
-- Table structure for table `attachments`
--

DROP TABLE IF EXISTS `attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attachments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `origin_name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `save_name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `file_path` varchar(500) COLLATE utf8mb4_general_ci NOT NULL,
  `file_size` int DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `post_id` (`post_id`),
  CONSTRAINT `attachments_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attachments`
--

LOCK TABLES `attachments` WRITE;
/*!40000 ALTER TABLE `attachments` DISABLE KEYS */;
INSERT INTO `attachments` VALUES (3,3,'20170306_203431.jpg','3ecdcfcda4984c2898a184c518156f04.jpg','uploads/3ecdcfcda4984c2898a184c518156f04.jpg',NULL,'2026-02-03 15:15:49'),(4,3,'20200123_193417.jpg','74111353c91740949d1f97dc32d53289.jpg','uploads/74111353c91740949d1f97dc32d53289.jpg',NULL,'2026-02-03 15:15:49'),(5,3,'20210418_122123.jpg','94f4fc509135493c8c1dc05341754f58.jpg','uploads/94f4fc509135493c8c1dc05341754f58.jpg',NULL,'2026-02-03 15:15:49'),(6,4,'김기원-개인정보보호법.pdf','340cd622d581477ca6cf288d4c246878.pdf','uploads/340cd622d581477ca6cf288d4c246878.pdf',NULL,'2026-02-03 15:17:25'),(7,5,'cats-8096304_1280.jpg','76853c592eec4f3a8047073028c02099.jpg','uploads/76853c592eec4f3a8047073028c02099.jpg',NULL,'2026-02-03 15:20:01'),(8,6,'파이썬 21일차, 4주차.txt','637e564976b5467f83141ad449567a4e.txt','uploads/637e564976b5467f83141ad449567a4e.txt',NULL,'2026-02-03 15:20:04'),(9,7,'귀여운 강쥐.jpg','c174c03590cd4d76b599eca106a22b76.jpg','uploads/c174c03590cd4d76b599eca106a22b76.jpg',NULL,'2026-02-03 15:20:23'),(10,8,'cbf3785bdc913ffa4bfefae21d3164d1.jpg','683f269d226a4a2eba57d68e3cf76b0d.jpg','uploads/683f269d226a4a2eba57d68e3cf76b0d.jpg',NULL,'2026-02-03 15:20:29'),(11,9,'다운로드.jpg','cb8b73b067754f0cb4fa096492ec4d6b.jpg','uploads/cb8b73b067754f0cb4fa096492ec4d6b.jpg',NULL,'2026-02-03 15:20:32'),(12,10,'화면 캡처 2026-02-03 151958.jpg','79ac3cfbd0fc4da1bee83ea89333abc0.jpg','uploads/79ac3cfbd0fc4da1bee83ea89333abc0.jpg',NULL,'2026-02-03 15:20:34'),(13,11,'0402-html.html','b4d3891618c34c81b0aa53af0f6b5207.html','uploads/b4d3891618c34c81b0aa53af0f6b5207.html',NULL,'2026-02-03 15:20:55'),(14,12,'8d11a368b5293315c34472224ff53600.jpg','ec59c083b9ed4b169815a5841f0cc5fd.jpg','uploads/ec59c083b9ed4b169815a5841f0cc5fd.jpg',NULL,'2026-02-03 15:21:01'),(15,13,'3. web_basic_bulidup.html','be2e3d3677344e28a7b62f4359cf0f1d.html','uploads/be2e3d3677344e28a7b62f4359cf0f1d.html',NULL,'2026-02-03 15:21:28'),(16,14,'0201-html.html','122bcdaae8474c928c50557d9606ed25.html','uploads/122bcdaae8474c928c50557d9606ed25.html',NULL,'2026-02-03 15:22:19'),(17,14,'0202-html.html','ad6de04805694aacb070cd4fdeb3d5f2.html','uploads/ad6de04805694aacb070cd4fdeb3d5f2.html',NULL,'2026-02-03 15:22:19'),(18,14,'0203-html.html','879b6a7b2fff4376a6cdfd456bb4c3ec.html','uploads/879b6a7b2fff4376a6cdfd456bb4c3ec.html',NULL,'2026-02-03 15:22:19'),(19,14,'0204-html.html','f2ccafaeda284feb881771cd60d3120a.html','uploads/f2ccafaeda284feb881771cd60d3120a.html',NULL,'2026-02-03 15:22:19'),(20,14,'0205-html.html','b3901678fc134575ae3436e7f97fb29f.html','uploads/b3901678fc134575ae3436e7f97fb29f.html',NULL,'2026-02-03 15:22:19'),(21,14,'0206-html.html','4f8c83e473234ef1931bf04a49cc727d.html','uploads/4f8c83e473234ef1931bf04a49cc727d.html',NULL,'2026-02-03 15:22:19'),(22,14,'0207-html.html','7e6529d8976c48bfaf2c7f3f3f1b7183.html','uploads/7e6529d8976c48bfaf2c7f3f3f1b7183.html',NULL,'2026-02-03 15:22:19'),(23,14,'0208-html.html','964129a106a5450bb369a0c626a1a47e.html','uploads/964129a106a5450bb369a0c626a1a47e.html',NULL,'2026-02-03 15:22:19'),(24,14,'0209-html.html','d5dbe2b4144c4d11b1b19d65e1bed09e.html','uploads/d5dbe2b4144c4d11b1b19d65e1bed09e.html',NULL,'2026-02-03 15:22:19'),(25,14,'0301-html.html','038c7981f78d41ad816fc9986d8a4c31.html','uploads/038c7981f78d41ad816fc9986d8a4c31.html',NULL,'2026-02-03 15:22:19'),(26,14,'0302-html.html','f65dbeed835d48ecac99192ce06cfd45.html','uploads/f65dbeed835d48ecac99192ce06cfd45.html',NULL,'2026-02-03 15:22:19'),(27,14,'0303-html.html','d22195159841406fb2c98f7b59ded9a0.html','uploads/d22195159841406fb2c98f7b59ded9a0.html',NULL,'2026-02-03 15:22:19'),(28,14,'0304-html.html','c749cb11dcfa4da4a48825ad246b5595.html','uploads/c749cb11dcfa4da4a48825ad246b5595.html',NULL,'2026-02-03 15:22:19'),(29,14,'0305-html.html','a00063edd5f74e30b7b2c202e228d321.html','uploads/a00063edd5f74e30b7b2c202e228d321.html',NULL,'2026-02-03 15:22:19'),(30,14,'0306-html.html','9390785db0c5464c8650f4a1463ad542.html','uploads/9390785db0c5464c8650f4a1463ad542.html',NULL,'2026-02-03 15:22:19'),(31,14,'0307-html.html','0634345e5e55405093a7b93783342d90.html','uploads/0634345e5e55405093a7b93783342d90.html',NULL,'2026-02-03 15:22:19'),(32,14,'0401-html.html','e958d82074474a1e8b53a3b0d7c84b80.html','uploads/e958d82074474a1e8b53a3b0d7c84b80.html',NULL,'2026-02-03 15:22:19'),(33,14,'0402-html.html','4823cf4c7bce4192a9da671e4302d1d3.html','uploads/4823cf4c7bce4192a9da671e4302d1d3.html',NULL,'2026-02-03 15:22:19'),(34,15,'60612a74efc091ae187f1ab6b43da108.jpg','f24aaec11ff64ca0b2e1c367450569b8.jpg','uploads/f24aaec11ff64ca0b2e1c367450569b8.jpg',NULL,'2026-02-03 15:22:23'),(35,15,'b0732fda05b2f5f8ed3bebf77c084da2.jpg','36bca843b07c45cc9bc9cb336a19dc55.jpg','uploads/36bca843b07c45cc9bc9cb336a19dc55.jpg',NULL,'2026-02-03 15:22:23'),(36,16,'귀여운 강쥐.jpg','930049a012df4de2a6b26e118e73a5be.jpg','uploads/930049a012df4de2a6b26e118e73a5be.jpg',NULL,'2026-02-03 15:24:12'),(43,18,'붙임1.2022년 직업능력개발훈련교사 향상훈련 서류 제출 안내.hwp','da6ae55f338a4751a415b6f64c2c05f6.hwp','uploads/da6ae55f338a4751a415b6f64c2c05f6.hwp',NULL,'2026-02-03 15:33:32'),(44,18,'붙임2. 2022년 자격교육 안내문(부록).hwp','2ffe6df5362a46289b7060b81456ffab.hwp','uploads/2ffe6df5362a46289b7060b81456ffab.hwp',NULL,'2026-02-03 15:33:32'),(45,18,'붙임3. 직업능력개발훈련교사 자격기준(개정전문)(제2020-176호, 20.12.31.).hwp','4698f011cab74234893841232d85bbd1.hwp','uploads/4698f011cab74234893841232d85bbd1.hwp',NULL,'2026-02-03 15:33:32'),(46,18,'붙임4. [참고자료]210426 경력인정에 대한 자가 체크리스트(향상훈련용).hwp','48388a3d14e24db896de3ac0ef24b8ac.hwp','uploads/48388a3d14e24db896de3ac0ef24b8ac.hwp',NULL,'2026-02-03 15:33:32');
/*!40000 ALTER TABLE `attachments` ENABLE KEYS */;
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
