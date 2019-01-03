-- create tables (if not already created by old php migrations)

-- TODO BM Temporary disabled.
-- disable warnings or mysql will complain about table exists and deprecated collate
-- SET sql_notes = 0;
--
-- CREATE TABLE IF NOT EXISTS `membership_members` (
--   `member_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
--   `email` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `password` varchar(60) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `firstname` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `lastname` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `civicregno` varchar(12) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `company` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `orgno` varchar(12) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `address_street` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `address_extra` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `address_zipcode` int(11) DEFAULT NULL,
--   `address_city` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `address_country` varchar(2) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `phone` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   `updated_at` datetime DEFAULT NULL,
--   `deleted_at` datetime DEFAULT NULL,
--   `member_number` int(11) NOT NULL,
--   PRIMARY KEY (`member_id`),
--   KEY `membership_members_email_index` (`email`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- CREATE TABLE IF NOT EXISTS `membership_groups` (
--   `group_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
--   `parent` int(11) NOT NULL,
--   `left` int(11) NOT NULL,
--   `right` int(11) NOT NULL,
--   `name` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `title` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `description` text COLLATE utf8mb4_0900_ai_ci,
--   `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   `updated_at` datetime DEFAULT NULL,
--   `deleted_at` datetime DEFAULT NULL,
--   PRIMARY KEY (`group_id`),
--   KEY `membership_groups_parent_index` (`parent`),
--   KEY `membership_groups_left_index` (`left`),
--   KEY `membership_groups_right_index` (`right`)
-- ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- CREATE TABLE IF NOT EXISTS `membership_permissions` (
--   `permission_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
--   `role_id` int(11) NOT NULL DEFAULT '0',
--   `permission` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `group_id` int(11) NOT NULL DEFAULT '0',
--   `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   `updated_at` datetime DEFAULT NULL,
--   `deleted_at` datetime DEFAULT NULL,
--   PRIMARY KEY (`permission_id`),
--   UNIQUE KEY `membership_permissions_permission_unique` (`permission`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- CREATE TABLE IF NOT EXISTS `membership_group_permissions` (
--   `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
--   `group_id` int(10) unsigned NOT NULL,
--   `permission_id` int(10) unsigned NOT NULL,
--   PRIMARY KEY (`id`),
--   UNIQUE KEY `membership_group_permissions_group_id_permission_id_unique` (`group_id`,`permission_id`),
--   KEY `membership_group_permissions_permission_id_foreign` (`permission_id`),
--   CONSTRAINT `membership_group_permissions_group_id_foreign` FOREIGN KEY (`group_id`) REFERENCES `membership_groups` (`group_id`),
--   CONSTRAINT `membership_group_permissions_permission_id_foreign` FOREIGN KEY (`permission_id`) REFERENCES `membership_permissions` (`permission_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- CREATE TABLE IF NOT EXISTS `membership_keys` (
--   `rfid_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
--   `member_id` int(10) unsigned NOT NULL,
--   `description` text COLLATE utf8mb4_0900_ai_ci,
--   `tagid` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   `updated_at` datetime DEFAULT NULL,
--   `deleted_at` datetime DEFAULT NULL,
--   PRIMARY KEY (`rfid_id`),
--   KEY `membership_keys_member_id_foreign` (`member_id`),
--   KEY `membership_keys_tagid_index` (`tagid`),
--   CONSTRAINT `membership_keys_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- CREATE TABLE IF NOT EXISTS `membership_members_groups` (
--   `member_id` int(11) NOT NULL,
--   `group_id` int(11) NOT NULL,
--   UNIQUE KEY `membership_members_groups_member_id_group_id_unique` (`member_id`,`group_id`),
--   KEY `membership_members_groups_member_id_index` (`member_id`),
--   KEY `membership_members_groups_group_id_index` (`group_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- -- TODO Remove this, force use of goups?
-- CREATE TABLE IF NOT EXISTS `membership_members_roles` (
--   `member_id` int(11) NOT NULL,
--   `role_id` int(11) NOT NULL,
--   KEY `membership_members_roles_member_id_index` (`member_id`),
--   KEY `membership_members_roles_role_id_index` (`role_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- -- TODO Remove this, force use of goups?
-- CREATE TABLE IF NOT EXISTS `membership_roles` (
--   `role_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
--   `group_id` int(11) NOT NULL,
--   `title` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `description` text COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   `updated_at` datetime DEFAULT NULL,
--   `deleted_at` datetime DEFAULT NULL,
--   PRIMARY KEY (`role_id`),
--   KEY `membership_roles_group_id_index` (`group_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- CREATE TABLE IF NOT EXISTS `membership_spans` (
--   `span_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
--   `member_id` int(10) unsigned NOT NULL,
--   `startdate` date NOT NULL,
--   `enddate` date NOT NULL,
--   `type` enum('labaccess','membership','special_labaccess') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
--   `creation_reason` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   `deleted_at` timestamp NULL DEFAULT NULL,
--   `deletion_reason` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
--   PRIMARY KEY (`span_id`),
--   KEY `membership_spans_member_id_foreign` (`member_id`),
--   KEY `membership_spans_span_id_index` (`span_id`),
--   CONSTRAINT `membership_spans_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
--
-- DROP TABLE IF EXISTS `migrations_membership`;
--
-- -- enable warnings
-- SET sql_notes = 1;

-- convert old existing tables to non deprecated char set and better collate
ALTER TABLE `membership_group_permissions` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_groups` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_keys` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_members` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_members_groups` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_members_roles` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_permissions` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_roles` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE `membership_spans` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- set updated at in database instead, TODO BM read back on save?
ALTER TABLE `membership_members` MODIFY COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE `membership_groups` MODIFY COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE `membership_permissions` MODIFY COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE `membership_keys` MODIFY COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE `membership_spans` MODIFY COLUMN `deleted_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- TODO BM Make unique fileds uniquie.
ALTER TABLE `membership_members` DROP INDEX `membership_members`;
-- TODO johank, approve this:
UPDATE `membership_members` SET email = 'athawolf@gmail.com-dedup' WHERE member_id = 1857 and email = 'athawolf@gmail.com';
UPDATE `membership_members` SET email = 'resdin@gmail.com-dedup-0' WHERE member_id = 1926 and email = 'resdin@gmail.com';
UPDATE `membership_members` SET email = 'resdin@gmail.com-dedup-1' WHERE member_id = 1927 and email = 'resdin@gmail.com';
ALTER TABLE `membership_members` ADD UNIQUE INDEX `membership_members_email_index` (`email`);
