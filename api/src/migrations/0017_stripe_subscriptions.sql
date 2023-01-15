--- add stripe id to webshop products
ALTER TABLE `webshop_products` ADD COLUMN `stripe_product_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

--- add session id from stripe to webshop transactions
--- ALTER TABLE `webshop_transactions` ADD COLUMN `stripe_session_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

ALTER TABLE `membership_members` ADD COLUMN `stripe_customer_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
ALTER TABLE `membership_members` ADD COLUMN `stripe_membership_subscription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
ALTER TABLE `membership_members` ADD COLUMN `stripe_labaccess_subscription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
