CREATE TABLE IF NOT EXISTS `webshop_accounting_exports` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `signer_member_id` int(10) unsigned NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `status` enum('completed','pending','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `aggregation` enum('year','month','day') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP NOT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `webshop_accounting_export_member_id_index` (`signer_member_id`),
  CONSTRAINT `webshop_accounting_export_member_id_foreign` FOREIGN KEY (`signer_member_id`) REFERENCES `membership_members` (`member_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
