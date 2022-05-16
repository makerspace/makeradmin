--- Too much work to keep the old data in the table so delete it
truncate table membership_box;

--- rename existing tables to something more fitting
RENAME TABLE `membership_box` TO `membership_storage`;
ALTER TABLE `membership_storage` RENAME COLUMN `box_label_id` TO `item_label_id`;
--- TODO foreing key stuff? index names?

--- drop unused columns
ALTER TABLE `membership_storage` DROP COLUMN `session_token`;
ALTER TABLE `membership_storage` DROP COLUMN `last_nag_at`;

--- add column for fixed end date of the allowed storage period which is used for some storage types
ALTER TABLE `membership_storage` ADD COLUMN `fixed_end_date` date DEFAULT NULL;

--- add template as "enum" to message, no real enum becuse too hard to maintain
ALTER TABLE `membership_storage` ADD COLUMN `storage_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

--- create a new table to store the nag history
CREATE TABLE `storage_nags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `item_label_id` bigint(20) unsigned NOT NULL,
  `nag_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  `nag_type` varchar(50) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  KEY `membership_storage_item_label_id_index` (`item_label_id`),
  KEY `membership_storage_member_id_index` (`member_id`),
  CONSTRAINT `storage_nags_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`),
  CONSTRAINT `storage_nags_item_label_id_foreign` FOREIGN KEY (`item_label_id`) REFERENCES `membership_storage` (`item_label_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
