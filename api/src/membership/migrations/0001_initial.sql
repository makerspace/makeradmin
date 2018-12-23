-- create tables

CREATE TABLE `membership_groups` (
  `group_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `parent` int(11) NOT NULL,
  `left` int(11) NOT NULL,
  `right` int(11) NOT NULL,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`group_id`),
  KEY `membership_groups_parent_index` (`parent`),
  KEY `membership_groups_left_index` (`left`),
  KEY `membership_groups_right_index` (`right`)
) ENGINE=InnoDB AUTO_INCREMENT=2;

CREATE TABLE `membership_group_permissions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `group_id` int(10) unsigned NOT NULL,
  `permission_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `membership_group_permissions_group_id_permission_id_unique` (`group_id`,`permission_id`),
  KEY `membership_group_permissions_permission_id_foreign` (`permission_id`),
  CONSTRAINT `membership_group_permissions_group_id_foreign` FOREIGN KEY (`group_id`) REFERENCES `membership_groups` (`group_id`),
  CONSTRAINT `membership_group_permissions_permission_id_foreign` FOREIGN KEY (`permission_id`) REFERENCES `membership_permissions` (`permission_id`)
) ENGINE=InnoDB;;

CREATE TABLE `membership_keys` (
  `rfid_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `description` text COLLATE utf8_unicode_ci,
  `tagid` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`rfid_id`),
  KEY `membership_keys_member_id_foreign` (`member_id`),
  KEY `membership_keys_tagid_index` (`tagid`),
  CONSTRAINT `membership_keys_member_id_foreign` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`)
) ENGINE=InnoDB;

