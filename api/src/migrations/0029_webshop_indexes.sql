ALTER TABLE `webshop_transactions` ADD INDEX `created_at_index` (`created_at`);
ALTER TABLE `webshop_transactions` ADD INDEX `member_id_index` (`member_id`);
ALTER TABLE `webshop_transaction_contents` ADD INDEX `product_id_index` (`product_id`);
