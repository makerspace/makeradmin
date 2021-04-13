-- disable warnings or mysql will complain about table exists and deprecated collate
SET sql_notes = 0;

-- create tables (if not already created by old php migrations)

CREATE TABLE IF NOT EXISTS `access_tokens` (
  `user_id` int(11) NOT NULL,
  `access_token` varchar(32) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `browser` varchar(512) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `ip` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `expires` datetime NOT NULL,
  `permissions` text COLLATE utf8mb4_0900_ai_ci,
  `lifetime` int(10) unsigned NOT NULL DEFAULT '300',
UNIQUE KEY `access_tokens_access_token_unique` (`access_token`),
KEY `access_tokens_user_id_index` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `login` (
  `success` tinyint(1) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `ip` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- drop tables that are no longer needed
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS relations;
DROP TABLE IF EXISTS migrations_apigateway;

-- enable warnings
SET sql_notes = 1;

-- convert old existing tables to non deprecated char set and better collate
ALTER TABLE `access_tokens` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `login` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
