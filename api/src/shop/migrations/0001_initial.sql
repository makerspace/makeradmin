-- create tables (if not already created by old webshop migrations)

-- disable warnings or mysql will complain about table exists and deprecated collate
SET sql_notes = 0;

CREATE TABLE IF NOT EXISTS `webshop_product_categories` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  `display_order` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `webshop_product_categories_display_order_unique` (`display_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_products` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `category_id` int(10) unsigned NOT NULL,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `unit` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `price` decimal(15,2) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  `smallest_multiple` int(10) NOT NULL DEFAULT '1',
  `filter` varchar(255) DEFAULT NULL,
  `image` varchar(255) DEFAULT NULL,
  `display_order` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `webshop_products_display_order_unique` (`display_order`),
  KEY `category_id_key` (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=62 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_product_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `action_id` int(10) unsigned NOT NULL,
  `value` int(10) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `product_constraint` (`product_id`),
  KEY `action_constraint` (`action_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_transactions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('pending','completed','failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_transaction_contents` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` int(10) unsigned NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `count` int(10) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `transaction_id_key` (`transaction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_transaction_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `content_id` int(10) unsigned NOT NULL,
  `action_id` int(10) unsigned NOT NULL,
  `value` int(10) DEFAULT NULL,
  `status` enum('pending','completed') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `content_key` (`content_id`),
  KEY `action_constraint3` (`action_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_pending_registrations` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `transaction_key` (`transaction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_product_images` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `caption` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `deleted_at` datetime DEFAULT NULL,
  `display_order` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `webshop_product_images_product_id_display_order_unique` (`product_id`,`display_order`),
  KEY `image_product_constraint` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `webshop_stripe_pending` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` int(10) unsigned NOT NULL,
  `stripe_token` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `token_key` (`stripe_token`),
  KEY `transaction_constraint2` (`transaction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `migrations_webshop`;
DROP TABLE IF EXISTS `webshop_product_variants`;

-- enable warnings
SET sql_notes = 1;

-- convert old existing tables to non deprecated char set and better collate
ALTER TABLE `webshop_pending_registrations` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_product_actions` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_product_categories` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_product_images` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_products` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_stripe_pending` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_transaction_actions` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_transaction_contents` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `webshop_transactions` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- add constraints that are missing in database.

ALTER TABLE `webshop_products` ADD CONSTRAINT `category_constraint` FOREIGN KEY (`category_id`) REFERENCES `webshop_product_categories` (`id`);
ALTER TABLE `webshop_product_actions` ADD CONSTRAINT `product_constraint` FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`);
ALTER TABLE `webshop_product_images` ADD CONSTRAINT `image_product_constraint` FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`);
ALTER TABLE `webshop_stripe_pending` ADD CONSTRAINT `transaction_constraint2` FOREIGN KEY (`transaction_id`) REFERENCES `webshop_transactions` (`id`);
ALTER TABLE `webshop_pending_registrations` ADD CONSTRAINT `transaction_constraint3` FOREIGN KEY (`transaction_id`) REFERENCES `webshop_transactions` (`id`);
ALTER TABLE `webshop_transaction_actions` ADD CONSTRAINT `content_constraint2` FOREIGN KEY (`content_id`) REFERENCES `webshop_transaction_contents` (`id`);
ALTER TABLE `webshop_transaction_contents` ADD CONSTRAINT `transaction_constraint` FOREIGN KEY (`transaction_id`) REFERENCES `webshop_transactions` (`id`);

-- replace action table with enum

ALTER TABLE `webshop_product_actions` ADD COLUMN `action_type` enum('add_membership_days','add_labaccess_days') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
UPDATE `webshop_product_actions` SET `action_type` = 'add_membership_days' where action_id = 1;
UPDATE `webshop_product_actions` SET `action_type` = 'add_labaccess_days' where action_id = 2;
ALTER TABLE `webshop_product_actions` DROP KEY `action_constraint`;
ALTER TABLE `webshop_product_actions` DROP COLUMN `action_id`;

ALTER TABLE `webshop_transaction_actions` ADD COLUMN `action_type` enum('add_membership_days','add_labaccess_days') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
UPDATE `webshop_transaction_actions` SET `action_type` = 'add_membership_days' where action_id = 1;
UPDATE `webshop_transaction_actions` SET `action_type` = 'add_labaccess_days' where action_id = 2;
ALTER TABLE `webshop_transaction_actions` DROP KEY `action_constraint3`;
ALTER TABLE `webshop_transaction_actions` DROP COLUMN `action_id`;

DROP TABLE `webshop_actions`


-- TODO Test if uniquie constraint gives same error messages as unique index.

