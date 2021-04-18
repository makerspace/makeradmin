-- add show column so product can be toggled as visible
ALTER TABLE `webshop_products` ADD COLUMN `show` boolean NOT NULL DEFAULT TRUE;
UPDATE `webshop_products` SET `show` = TRUE;
