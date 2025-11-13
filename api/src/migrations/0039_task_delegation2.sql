UPDATE task_delegation_log SET card_id = template_card_id WHERE template_card_id IS NOT NULL;
ALTER TABLE task_delegation_log DROP COLUMN template_card_id;
