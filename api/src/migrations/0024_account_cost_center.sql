CREATE TABLE IF NOT EXISTS `webshop_transaction_accounts` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `account` int(10) unsigned NOT NULL UNIQUE,
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_order` int(10) unsigned NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `webshop_transaction_accounts_display_order_unique` (`display_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_transaction_cost_centers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cost_center` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL UNIQUE,
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `display_order` int(10) unsigned NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `webshop_transaction_cost_centers_display_order_unique` (`display_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_product_accounting` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `account_id` int(10) unsigned NOT NULL,
  `cost_center_id` int(10) unsigned NOT NULL,
  `debits` decimal(10,2) unsigned NOT NULL DEFAULT 0,
  `credits` decimal(10,2) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `account_id_key` (`account_id`),
  CONSTRAINT `webshop_product_accounting_account_id_foreign` FOREIGN KEY (`account_id`) REFERENCES `webshop_transaction_accounts` (`id`),
  KEY `cost_center_id_key` (`cost_center_id`),
  CONSTRAINT `webshop_product_accounting_cost_center_id_foreign` FOREIGN KEY (`cost_center_id`) REFERENCES `webshop_transaction_cost_centers` (`id`),
  KEY `webshop_product_accounting_id_index` (`product_id`),
  CONSTRAINT `webshop_product_accounting_product_id_foreign` FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;