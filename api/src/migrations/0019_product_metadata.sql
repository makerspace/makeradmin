ALTER TABLE `webshop_products` ADD COLUMN `product_metadata` json;
UPDATE `webshop_products` SET `product_metadata` = '{}';
ALTER TABLE `webshop_products` MODIFY COLUMN `product_metadata` json NOT NULL DEFAULT ('{}');
