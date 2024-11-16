-- Create new table for discounts
CREATE TABLE IF NOT EXISTS `webshop_discounts`(
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `percent_off` int(5) NOT NULL,
    `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `duration` enum('forever','once','repeating') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `duration_in_months` int(10) unsigned DEFAULT NULL,
    `stripe_coupon_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    `display_order` int(10) unsigned NOT NULL,
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` datetime DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `discounts_display_order_unique` (`display_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create new table for which products the discount applies to
CREATE TABLE IF NOT EXISTS `webshop_discount_product_mapping` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `discount_id` int(10) unsigned,
  PRIMARY KEY (`id`),
  KEY `discount_id_key` (`discount_id`),
  CONSTRAINT `webshop_discount_product_mapping_discount_id_foreign` FOREIGN KEY (`discount_id`) REFERENCES `webshop_discounts` (`id`),
  KEY `product_id_key` (`product_id`),
  CONSTRAINT `webshop_discount_product_mapping_product_id_foreign` FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
