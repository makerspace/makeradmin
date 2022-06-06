--- create a new table to store the request for change phone numbers
CREATE TABLE IF NOT EXISTS `change_phone_number_requests` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `completed` boolean DEFAULT false NOT NULL,
  `time_stamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `change_phone_number_member_id_index` (`member_id`),
  CONSTRAINT `change_phone_number_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;