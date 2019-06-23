
--- drop unused columns
ALTER TABLE `messages_recipient` DROP FOREIGN KEY `messages_recipient_messages_message_id_foreign`;
ALTER TABLE `messages_recipient` DROP COLUMN `messages_message_id`;

--- drop unused tables
DROP TABLE `messages_template`;
DROP TABLE `messages_message`;

--- rename existing tables to something more fitting
RENAME TABLE `messages_recipient` TO `message`;

--- rename columns in tables to better names
ALTER TABLE `message` RENAME COLUMN `messages_recipient_id` TO `id`;
ALTER TABLE `message` RENAME COLUMN `title` TO `subject`;
ALTER TABLE `message` RENAME COLUMN `description` TO `body`;
ALTER TABLE `message` RENAME COLUMN `date_sent` TO `sent_at`;

--- add template as "enum" to message, no real enum becuse too hard to maintain
ALTER TABLE `message` ADD COLUMN `template` varchar(112) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

--- change varchar columns to text
ALTER TABLE `message` MODIFY COLUMN `subject` text COLLATE utf8mb4_0900_ai_ci NOT NULL;

--- change varchar columns to enum
ALTER TABLE `message` MODIFY COLUMN `status` enum('sent', 'queued', 'failed') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL;
