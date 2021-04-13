-- extend user agent max length (have found valid user agents with up to 280 characters in length)
ALTER TABLE `access_tokens` MODIFY COLUMN `browser` varchar(512) COLLATE utf8mb4_0900_ai_ci NOT NULL;
