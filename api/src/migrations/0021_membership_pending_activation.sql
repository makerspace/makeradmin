ALTER TABLE membership_members ADD COLUMN `pending_activation` boolean;
UPDATE membership_members SET pending_activation = false;
ALTER TABLE membership_members MODIFY COLUMN `pending_activation` boolean NOT NULL;
