-- Add option to control whether help notifications are sent when a member completes a quiz
-- Defaults to true (1) so existing quizzes will have notifications enabled

ALTER TABLE quiz_quizzes ADD COLUMN send_help_notifications BOOLEAN NOT NULL DEFAULT TRUE;
