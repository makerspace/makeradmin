CREATE TABLE `webshop_product_categories` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
);

# Replaced below
CREATE TABLE `webshop_product_images` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `path` varchar(255) COLLATE utf8mb4_unicode_ci,
  `caption` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`)
);

CREATE TABLE `webshop_products` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `category_id` int(10) unsigned NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `unit` varchar(30) COLLATE utf8mb4_unicode_ci,
  `price` decimal(15,2) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id_key` (category_id),
  CONSTRAINT category_constraint FOREIGN KEY (`category_id`) REFERENCES `webshop_product_categories` (`id`)
);

CREATE TABLE `webshop_product_variants` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci,
  `price` decimal(15,2) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `webshop_transactions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);

CREATE TABLE `webshop_transaction_contents` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` int(10) unsigned NOT NULL,
  `product_id` int(10) unsigned NOT NULL,
  `count` int(10) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `transaction_id_key` (transaction_id),
  CONSTRAINT transaction_constraint FOREIGN KEY (`transaction_id`) REFERENCES `webshop_transactions` (`id`)
);

ALTER TABLE `webshop_products` ADD `action` varchar(255);
ALTER TABLE `webshop_transaction_contents` ADD `completed` int(1) NOT NULL;
ALTER TABLE `webshop_products` ADD `smallest_multiple` int(10) NOT NULL DEFAULT 1;

ALTER TABLE `webshop_products` DROP `action`;
ALTER TABLE `webshop_transaction_contents` DROP `completed`;

CREATE TABLE `webshop_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `webshop_product_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `action_id` int(10) unsigned NOT NULL,
  `value` int(10),
  PRIMARY KEY (`id`),
  CONSTRAINT product_constraint FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`),
  CONSTRAINT action_constraint FOREIGN KEY (`action_id`) REFERENCES `webshop_actions` (`id`)
);

CREATE TABLE `webshop_completed_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `content_id` int(10) unsigned NOT NULL,
  `action_id` int(10) unsigned NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  CONSTRAINT content_constraint FOREIGN KEY (`content_id`) REFERENCES `webshop_transaction_contents` (`id`),
  CONSTRAINT action_constraint2 FOREIGN KEY (`action_id`) REFERENCES `webshop_product_actions` (`id`)
);

INSERT INTO webshop_actions (name) VALUES('add_membership_days');
INSERT INTO webshop_actions (name) VALUES('add_labaccess_days');

ALTER TABLE `webshop_product_actions` ADD `created_at` datetime DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE `webshop_product_actions` ADD `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE `webshop_product_actions` ADD `deleted_at` datetime DEFAULT NULL;

ALTER TABLE `webshop_transactions` ADD `status` enum('pending','completed', 'failed') COLLATE utf8mb4_unicode_ci NOT NULL;

# For stripe
CREATE TABLE `webshop_stripe_pending` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` int(10) unsigned NOT NULL,
  `stripe_token` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `token_key` (stripe_token),
  CONSTRAINT transaction_constraint2 FOREIGN KEY (`transaction_id`) REFERENCES `webshop_transactions` (`id`)
);

CREATE TABLE `webshop_pending_registrations` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `transaction_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `transaction_key` (transaction_id),
  CONSTRAINT transaction_constraint3 FOREIGN KEY (`transaction_id`) REFERENCES `webshop_transactions` (`id`)
);

CREATE TABLE `webshop_transaction_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `content_id` int(10) unsigned NOT NULL,
  `action_id` int(10) unsigned NOT NULL,
  `value` int(10),
  `status` enum('pending','completed') COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `content_key` (content_id),
  CONSTRAINT content_constraint2 FOREIGN KEY (`content_id`) REFERENCES `webshop_transaction_contents` (`id`),
  CONSTRAINT action_constraint3 FOREIGN KEY (`action_id`) REFERENCES `webshop_actions` (`id`)
);

DROP TABLE webshop_completed_actions;

ALTER TABLE `webshop_transaction_actions` ADD `completed_at` datetime DEFAULT NULL;

ALTER TABLE `webshop_products` ADD `filter` varchar(255) DEFAULT NULL;

DROP TABLE IF EXISTS `webshop_product_images`;
CREATE TABLE `webshop_product_images` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `caption` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT image_product_constraint FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`)
);
