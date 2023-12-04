-- Create new table for gift cards
CREATE TABLE IF NOT EXISTS `webshop_gift_card`(
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `amount` decimal(15,2) NOT NULL,
    `validation_code` VARCHAR(16) unique COLLATE utf8mb4_0900_ai_ci NOT NULL,
    `email` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
    `status` enum('pending','activated','expired') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create new table for Product and Gift Card mapping
CREATE TABLE IF NOT EXISTS `webshop_product_gift_card_mapping` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `gift_card_id` int(11) unsigned NOT NULL,
    `product_id` int(10) unsigned NOT NULL,
    `product_quantity` int(10) unsigned NOT NULL,
    `amount` decimal(15,2) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `gift_card_id_index` (`gift_card_id`),
    CONSTRAINT `gift_card_id_foreign` FOREIGN KEY (`gift_card_id`) REFERENCES `webshop_gift_card` (`id`),
    KEY `product_id_index` (`product_id`),
    CONSTRAINT `product_id_foreign` FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Make member_id nullable in Transactions, to enable Gift card purchasable without being a member
ALTER TABLE `webshop_transactions` MODIFY COLUMN member_id int(10) unsigned NULL;