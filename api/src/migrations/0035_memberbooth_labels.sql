CREATE TABLE IF NOT EXISTS `memberbooth_labels` (
  `id` bigint(20) unsigned NOT NULL,
  `member_id` int(10) unsigned NOT NULL,
  `data` JSON,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP NOT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `memberbooth_labels_member_id_index` (`member_id`),
  CONSTRAINT `memberbooth_labels_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`)
);

CREATE TABLE IF NOT EXISTS `memberbooth_labels_actions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `label_id` bigint(20) unsigned NOT NULL,
  `action_member_id` int(10) unsigned NOT NULL,
  `session_token` varchar(32) NOT NULL,
  `action` ENUM('observed','reported','cleaned_away') NOT NULL,
  `message` TEXT DEFAULT NULL,
  `image` BLOB DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (`id`),
  KEY `memberbooth_labels_actions_session_token_index` (`session_token`),
  KEY `memberbooth_labels_actions_action_member_id_index` (`action_member_id`),
  CONSTRAINT `memberbooth_labels_actions_member_id_foreign` FOREIGN KEY (`action_member_id`) REFERENCES `membership_members` (`member_id`),
  CONSTRAINT `memberbooth_labels_actions_label_id_foreign` FOREIGN KEY (`label_id`) REFERENCES `memberbooth_labels` (`id`)
);
