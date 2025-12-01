ALTER TABLE task_delegation_log
MODIFY COLUMN action ENUM(
    'assigned',
    'completed',
    'not_done_did_something_else',
    'not_done_confused',
    'not_done_forgot',
    'not_done_no_time',
    'not_done_other',
    'ignored',
    'already_completed_by_someone_else'
) NOT NULL;
