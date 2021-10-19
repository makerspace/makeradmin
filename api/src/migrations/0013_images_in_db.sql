ALTER TABLE `webshop_product_images` DROP FOREIGN KEY `image_product_constraint`;
ALTER TABLE `webshop_product_images` DROP COLUMN `product_id`;
ALTER TABLE `webshop_product_images` DROP COLUMN `path`;
ALTER TABLE `webshop_product_images` DROP COLUMN `caption`;
ALTER TABLE `webshop_product_images` DROP COLUMN `display_order`;
ALTER TABLE `webshop_product_images` ADD COLUMN `name` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL;
ALTER TABLE `webshop_product_images` ADD COLUMN `type` varchar(64) COLLATE utf8mb4_0900_ai_ci NOT NULL;
ALTER TABLE `webshop_product_images` ADD COLUMN `data` BLOB NOT NULL;
ALTER TABLE `webshop_product_images` ADD COLUMN `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE `webshop_product_images` ADD COLUMN `updated_at` datetime DEFAULT NULL;

ALTER TABLE `webshop_products` DROP COLUMN `image`;
ALTER TABLE `webshop_products` ADD COLUMN `image_id` int unsigned;
ALTER TABLE `webshop_products` ADD CONSTRAINT `image_constraint` FOREIGN KEY (`image_id`) REFERENCES `webshop_product_images` (`id`);
