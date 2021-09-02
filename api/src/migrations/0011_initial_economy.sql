-- enable warnings
SET sql_notes = 1;

CREATE TABLE IF NOT EXISTS `economy_expenses` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  `amount` TEXT NOT NULL,
  `payment_type` ENUM('paid_self', 'makerspace_to_pay_invoice', 'paid_by_makerspace') NOT NULL,
  `target_bank_account` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE IF NOT EXISTS `economy_files` (
  -- content id, this is the sha1 hash of the `file_name` field, `mime_type` field and `data` fields concatenated together.
  `cid` binary(20) NOT NULL,
  `file_name` TEXT NOT NULL,
  -- mime type
  `mime_type` TEXT NOT NULL,
  `data` LONGBLOB NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`cid`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `economy_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` TEXT NOT NULL,
  -- Note: must be immutable. Otherwise if groups are changed then previous expenses could get fractions that do not add up to 1 in each group
  `group` TEXT NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tags assigned to the expenses
CREATE TABLE IF NOT EXISTS `economy_expense_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `expense_id` int(10) unsigned NOT NULL,
  `tag_id` int(10) unsigned NOT NULL,
  `fraction` tinyint unsigned NOT NULL, -- value between 0 and 255 representing a percentage
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),

  KEY `expense_id_key` (`expense_id`),
  KEY `tag_id_key` (`tag_id`),
  CONSTRAINT `tag_expenses_constraint` FOREIGN KEY (`expense_id`) REFERENCES `economy_expenses` (`id`),
  CONSTRAINT `tag_tag_constraint` FOREIGN KEY (`tag_id`) REFERENCES `economy_tags` (`id`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- files assigned to the expenses
CREATE TABLE IF NOT EXISTS `economy_expense_files` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `expense_id` int(10) unsigned NOT NULL,
  `file_cid` binary(20) unsigned NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),

  KEY `expense_id_key` (`expense_id`),
  KEY `file_cid` (`file_cid`),
  CONSTRAINT `file_expenses_constraint` FOREIGN KEY (`expense_id`) REFERENCES `economy_expenses` (`id`),
  CONSTRAINT `file_file_constraint` FOREIGN KEY (`file_cid`) REFERENCES `economy_files` (`cid`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

