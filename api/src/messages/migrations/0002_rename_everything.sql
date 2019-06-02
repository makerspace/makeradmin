
--- drop unused template table
DROP TABLE `messages_template`;

--- rename existing tables to something more fitting
RENAME TABLE `messages_message` TO `message_template`;
RENAME TABLE `messages_recipient` TO `message`;

--- rename columns in tables to better names
ALTER TABLE `message_template` RENAME COLUMN `messages_message_id` TO `id`;
ALTER TABLE `message_template` RENAME COLUMN `title` TO `subject`;
ALTER TABLE `message_template` RENAME COLUMN `description` TO `body`;
ALTER TABLE `message` RENAME COLUMN `messages_recipient_id` TO `id`;
ALTER TABLE `message` RENAME COLUMN `messages_message_id` TO `message_template_id`;
ALTER TABLE `message` RENAME COLUMN `title` TO `subject`;
ALTER TABLE `message` RENAME COLUMN `description` TO `body`;

--- drop unused columns
ALTER TABLE `message_template` DROP COLUMN `message_type`;
ALTER TABLE `message_template` DROP COLUMN `status`;

--- add purpose table to message template
ALTER TABLE `message_template` ADD COLUMN `purpose` enum('labaccess_reminder') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `message` ADD COLUMN `purpose` enum('labaccess_reminder') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

--- change varchar columns to text
ALTER TABLE `message_template` MODIFY COLUMN `subject` text COLLATE utf8mb4_0900_ai_ci NOT NULL;
ALTER TABLE `message` MODIFY COLUMN `subject` text COLLATE utf8mb4_0900_ai_ci NOT NULL;

--- change varchar columns to enum
ALTER TABLE `message` MODIFY COLUMN `status` enum('sent', 'queued', 'failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL;
