--- Too much work to keep the old data in the table so delete it
drop table IF EXISTS membership_box;

--- create a new table to store the storage types
CREATE TABLE IF NOT EXISTS `storage_types` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `storage_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_order` int(10) unsigned NOT NULL,
  `has_fixed_end_date` boolean NOT NULL,
  `number_of_days` int(10) unsigned NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `storage_types_display_order_unique` (`display_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--- create a new table to store the message types
CREATE TABLE IF NOT EXISTS `storage_message_types` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `message_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_order` int(10) unsigned NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `storage_message_types_display_order_unique` (`display_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--- create a new table to store the items instead of the old one
CREATE TABLE IF NOT EXISTS `storage_items` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `members_description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `member_id` int(10) unsigned NOT NULL,
  `item_label_id` bigint(20) unsigned NOT NULL,
  `last_check_at` datetime DEFAULT NULL,
  `fixed_end_date` datetime DEFAULT NULL,
  `storage_type_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `storage_items_label_id_index` (`item_label_id`),
  KEY `storage_items_member_id_index` (`member_id`),
  CONSTRAINT `storage_items_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`),
  KEY `storage_type_id_key` (`storage_type_id`),
  CONSTRAINT `storage_types_id_key_foreign` FOREIGN KEY (`storage_type_id`) REFERENCES `storage_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--- create a new table to store the message history
CREATE TABLE IF NOT EXISTS `storage_messages` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `storage_item_id` int(10) unsigned NOT NULL,
  `message_at` datetime NOT NULL,
  `message_type_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `storage_item_id_key` (`storage_item_id`),
  CONSTRAINT `storage_messages_storage_item_id_foreign` FOREIGN KEY (`storage_item_id`) REFERENCES `storage_items` (`id`),
  KEY `member_id_key` (`member_id`),
  CONSTRAINT `storage_messages_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`),
  KEY `message_type_id_key` (`message_type_id`),
  CONSTRAINT `storage_messages_message_type_id_foreign` FOREIGN KEY (`message_type_id`) REFERENCES `storage_message_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
