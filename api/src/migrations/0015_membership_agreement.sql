--- Timestamp for when the labaccess agreement was signed by the member.
ALTER TABLE `membership_members` ADD COLUMN `labaccess_agreement_at`  datetime;

--- Set labaccess agreement for existing members.
UPDATE membership_members SET labaccess_agreement_at = now() WHERE member_id in (SELECT member_id FROM membership_keys);
