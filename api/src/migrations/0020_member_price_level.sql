ALTER TABLE `membership_members` ADD COLUMN `price_level` ENUM('normal', 'low_income_discount');
ALTER TABLE `membership_members` ADD COLUMN `price_level_motivation` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
UPDATE `membership_members` SET `price_level` = 'normal';
ALTER TABLE `membership_members` MODIFY COLUMN `price_level` ENUM('normal', 'low_income_discount') NOT NULL DEFAULT 'normal';
