CREATE TABLE IF NOT EXISTS `membership_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `group_id` int(10) unsigned NOT NULL,
  `tag` varchar(255) UNIQUE COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tag_group_id_index` (`group_id`),
  CONSTRAINT `tag_group_id_foreign` FOREIGN KEY (`group_id`) REFERENCES `membership_groups` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;