ALTER TABLE `membership_members` ADD COLUMN `stripe_customer_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
ALTER TABLE `membership_members` ADD COLUMN `stripe_membership_subscription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
ALTER TABLE `membership_members` ADD COLUMN `stripe_labaccess_subscription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
