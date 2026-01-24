-- Add 'slack' as a recipient type for messages
ALTER TABLE `message` MODIFY COLUMN `recipient_type` ENUM('email', 'sms', 'slack') NOT NULL;
