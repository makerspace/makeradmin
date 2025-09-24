ALTER TABLE `message` ADD COLUMN `associated_id` BIGINT DEFAULT NULL;
ALTER TABLE `message` ADD COLUMN `recipient_type` ENUM('email', 'sms') DEFAULT NULL;
UPDATE `message` SET `recipient_type` = 'email';
ALTER TABLE `message` MODIFY COLUMN `recipient_type` ENUM('email', 'sms') NOT NULL;
ALTER TABLE `message` MODIFY COLUMN `recipient` VARCHAR(255) NOT NULL;
ALTER TABLE `message` MODIFY COLUMN `body` mediumtext NOT NULL;
CREATE INDEX idx_message_associated_id ON `message` (`associated_id`);
