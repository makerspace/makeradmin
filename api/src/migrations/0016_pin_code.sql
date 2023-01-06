--- Pin code for logging into e.g. memberbooth
ALTER TABLE `membership_members` ADD COLUMN `pin_code` varchar(30);

--- Randomize a unique pin code for existing members
SET @pin_length = 4;
UPDATE membership_members SET pin_code = LPAD(FLOOR(POW(10,@pin_length) * RAND()), @pin_length, 0) where pin_code is NULL;
