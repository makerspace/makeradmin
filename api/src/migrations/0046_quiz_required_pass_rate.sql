-- Add optional required_pass_rate column to quiz_quizzes
-- This allows quizzes to have a minimum pass rate requirement.
-- If a member has more than (1 - required_pass_rate) * total_questions incorrect answers, they fail.

ALTER TABLE quiz_quizzes ADD COLUMN required_pass_rate FLOAT DEFAULT 0.8;
