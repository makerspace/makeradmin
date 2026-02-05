-- Add visible field to quiz_quizzes table to control quiz visibility to members
ALTER TABLE quiz_quizzes ADD COLUMN visible BOOLEAN NOT NULL DEFAULT TRUE;
