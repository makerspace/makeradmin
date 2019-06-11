
--- drop unused columns
ALTER TABLE `message_recipient` DROP COLUMN `message_template_id`;
ALTER TABLE `message_recipient` DROP COLUMN `message_type`;
ALTER TABLE `message_recipient` DROP COLUMN `status`;

--- drop unused template table
DROP TABLE `messages_template`;
DROP TABLE `messages_message`;

--- rename existing tables to something more fitting
RENAME TABLE `messages_recipient` TO `message`;

--- rename columns in tables to better names
ALTER TABLE `message` RENAME COLUMN `messages_recipient_id` TO `id`;
ALTER TABLE `message` RENAME COLUMN `title` TO `subject`;
ALTER TABLE `message` RENAME COLUMN `description` TO `body`;

--- add purpose table to message template
ALTER TABLE `message` ADD COLUMN `template` enum('labaccess_reminder') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

--- change varchar columns to text
ALTER TABLE `message` MODIFY COLUMN `subject` text COLLATE utf8mb4_0900_ai_ci NOT NULL;

--- change varchar columns to enum
ALTER TABLE `message` MODIFY COLUMN `status` enum('sent', 'queued', 'failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL;
