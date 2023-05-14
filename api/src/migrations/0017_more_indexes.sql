ALTER TABLE `membership_spans` ADD INDEX `end_date_index` (`enddate`);
ALTER TABLE `message` ADD INDEX `member_id_index` (`member_id`);
ALTER TABLE `message` ADD INDEX `status_index` (`status`);
