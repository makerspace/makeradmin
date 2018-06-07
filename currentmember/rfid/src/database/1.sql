CREATE TABLE IF NOT EXISTS `rfid` (
  `rfid_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `title` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
    `description` text COLLATE utf8_unicode_ci,
    `tagid` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `status` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `startdate` datetime DEFAULT NULL,
    `enddate` datetime DEFAULT NULL,
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` datetime DEFAULT NULL,
    PRIMARY KEY (`rfid_id`),
    KEY `rfid_tagid_index` (`tagid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `rfid` CHANGE `rfid_id` `id` int(10) unsigned NOT NULL AUTO_INCREMENT;
ALTER TABLE `rfid` CHANGE `updated_at` `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
