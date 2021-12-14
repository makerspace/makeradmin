--- drop unused columns
ALTER TABLE `membership_box` DROP COLUMN `session_token`;
ALTER TABLE `membership_box` DROP COLUMN `last_nag_at`;

--- rename existing tables to something more fitting
RENAME TABLE `membership_box` TO `membership_storage`;

--- add template as "enum" to message, no real enum becuse too hard to maintain
ALTER TABLE `membership_storage` ADD COLUMN `storage_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

--- create a new table to store the nag history
CREATE TABLE `storage_nags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `box_label_id` bigint(20) unsigned NOT NULL,
  `nag_at` datetime NOT NULL,
  'nag_type' VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `membership_box_tag_id_index` (`box_label_id`),
  KEY `membership_box_member_id_index` (`member_id`),
  CONSTRAINT `membership_box_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
