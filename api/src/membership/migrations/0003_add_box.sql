CREATE TABLE `membership_box` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `box_label_id` int(20) unsigned NOT NULL,
  `session_token` varchar(32) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `last_nag_at` datetime DEFAULT NULL,
  `last_check_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `membership_box_tag_id_index` (`box_label_id`),
  KEY `membership_box_session_token_index` (`session_token`),
  KEY `membership_box_member_id_index` (`member_id`),
  CONSTRAINT `membership_box_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
