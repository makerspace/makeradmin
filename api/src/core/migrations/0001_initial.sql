-- create tables (if not already created by old php migrations)

-- disable warnings or mysql will complain about table exists and deprecated collate
SET sql_notes = 0;

CREATE TABLE IF NOT EXISTS `access_tokens` (
  `user_id` int(11) NOT NULL,
  `access_token` varchar(32) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `browser` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
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

DROP TABLE IF EXISTS `migrations_apigateway`;

-- TODO Remove when api-gateway is removed, but keep it until then beacuse api-gateway can't survive without it.
CREATE TABLE  IF NOT EXISTS `services` (
  `service_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `url` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `endpoint` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `version` varchar(12) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`service_id`),
  KEY `services_url_index` (`url`),
  KEY `services_version_index` (`version`),
  KEY `services_deleted_at_index` (`deleted_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- TODO Remove when api-gateway is removed, but keep it until then beacuse api-gateway can't survive without it.
CREATE TABLE IF NOT EXISTS `relations` (
  `url1` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `url2` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- enable warnings
SET sql_notes = 1;

-- convert old existing tables to non deprecated char set and better collate
ALTER TABLE `access_tokens` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `login` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- TODO remove obsolete tables (when not needed, in new migration)
-- TODO DROP TABLE services;
-- TODO DROP TABLE relations;
-- TODO DROP TABLE migrations_apigateway
