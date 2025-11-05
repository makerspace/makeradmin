CREATE TABLE task_delegation_log (
    id SERIAL PRIMARY KEY, -- TODO: Use UUID or something to avoid enumeration attacks
    member_id INT UNSIGNED REFERENCES membership_members(member_id),
    card_id VARCHAR(128) NOT NULL,
    card_name TEXT NOT NULL,
    action ENUM('assigned', 'completed', 'not_done_did_something_else', 'not_done_confused', 'not_done_forgot', 'not_done_no_time', 'not_done_other', 'ignored') NOT NULL,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    KEY member_id (member_id),
    KEY created_at (created_at),
    KEY member_id_created_at (member_id, created_at)
);

CREATE TABLE task_delegation_log_labels (
    id SERIAL PRIMARY KEY,
    log_id BIGINT UNSIGNED NOT NULL REFERENCES task_delegation_log(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    KEY log_id (log_id)
);
