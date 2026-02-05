-- Add table for storing custom Slack email addresses
CREATE TABLE slack_email_override (
    member_id INT UNSIGNED PRIMARY KEY REFERENCES membership_members(member_id) ON DELETE CASCADE,
    slack_email VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    KEY slack_email (slack_email)
);
