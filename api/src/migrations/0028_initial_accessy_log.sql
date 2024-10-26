-- Create new table for physcial access, like opening doors
CREATE TABLE IF NOT EXISTS `physical_access_log`(
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `member_id` int unsigned, -- Makerspace member id. Can be null if we cannot associate the access to a member. Can also be null if the data has been anonymized.
    `accessy_user_id` varchar(255) COLLATE utf8mb4_0900_ai_ci, -- Accessy user id. Can be null if the data has been anonymized.
    `accessy_asset_operation_id` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
    `accessy_asset_publication_id` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
    `invoked_at` datetime NOT NULL,
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `member_id_key` (`member_id`),
    KEY `invoked_at_key` (`invoked_at`),
    CONSTRAINT `physical_access_member_constraint` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
