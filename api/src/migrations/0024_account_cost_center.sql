CREATE TABLE IF NOT EXISTS `webshop_accounts_cost_centers` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` int(10) unsigned NOT NULL,
  `cost_center` int(10) unsigned NOT NULL,
  `account` int(10) unsigned NOT NULL,
  `debits` decimal(10,2) unsigned,
  `credits` decimal(10,2) unsigned,
  PRIMARY KEY (`id`),
  KEY `webshop_accounts_cost_centers_id_index` (`product_id`),
  CONSTRAINT `webshop_accounts_cost_centers_product_id_foreign` FOREIGN KEY (`product_id`) REFERENCES `webshop_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
