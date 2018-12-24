-- create tables (if not already created by old php migrations)

-- disable warnings or mysql will complain about table exists and deprecated collate
SET sql_notes = 0;

CREATE TABLE IF NOT EXISTS `messages_message` (
  `messages_message_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` text COLLATE utf8mb4_0900_ai_ci,
  `message_type` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`messages_message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `messages_recipient` (
  `messages_recipient_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `messages_message_id` int(10) unsigned NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` text COLLATE utf8mb4_0900_ai_ci,
  `member_id` int(11) DEFAULT NULL,
  `recipient` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `date_sent` datetime DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`messages_recipient_id`),
  KEY `messages_recipient_messages_message_id_foreign` (`messages_message_id`),
  CONSTRAINT `messages_recipient_messages_message_id_foreign` FOREIGN KEY (`messages_message_id`) REFERENCES `messages_message` (`messages_message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `messages_template` (
  `messages_template_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` text COLLATE utf8mb4_0900_ai_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`messages_template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `migrations_messages`;

-- enable warnings
SET sql_notes = 1;

-- convert old existing tables to non deprecated char set and better collate
ALTER TABLE `messages_message` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `messages_recipient` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `messages_template` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
