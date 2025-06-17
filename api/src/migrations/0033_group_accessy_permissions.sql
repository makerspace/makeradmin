CREATE TABLE IF NOT EXISTS `membership_group_door_access` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `group_id` int(10) unsigned NOT NULL,
  `accessy_asset_publication_guid` VARCHAR(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `membership_group_doors_group_id_index` (`group_id`),
  CONSTRAINT `membership_groups_foreign` FOREIGN KEY (`group_id`) REFERENCES `membership_groups` (`group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
