-- Migration to add quiz attempt tracking for retakes
-- Allows members to retake quizzes while preserving all historical answers

-- Create table for quiz attempts (each time a member starts/restarts a quiz)
CREATE TABLE IF NOT EXISTS `quiz_attempts` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `member_id` int(10) unsigned NOT NULL,
  `quiz_id` int(10) unsigned NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `member_id_key` (`member_id`),
  KEY `quiz_id_key` (`quiz_id`),
  CONSTRAINT `attempt_member_constraint` FOREIGN KEY (`member_id`) REFERENCES `membership_members` (`member_id`),
  CONSTRAINT `attempt_quiz_constraint` FOREIGN KEY (`quiz_id`) REFERENCES `quiz_quizzes` (`id`)
);

-- Add attempt_id column to quiz_answers table (nullable for backwards compatibility with existing answers)
ALTER TABLE `quiz_answers` ADD COLUMN `attempt_id` int(10) unsigned DEFAULT NULL;
ALTER TABLE `quiz_answers` ADD KEY `attempt_id_key` (`attempt_id`);
ALTER TABLE `quiz_answers` ADD CONSTRAINT `answer_attempt_constraint` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`);

-- Create initial attempts for all existing members who have answers
-- This groups existing answers under "attempt 1" for each member+quiz combination
INSERT INTO `quiz_attempts` (`member_id`, `quiz_id`, `created_at`)
SELECT DISTINCT qa.member_id, qq.quiz_id, MIN(qa.created_at)
FROM quiz_answers qa
JOIN quiz_questions qq ON qa.question_id = qq.id
GROUP BY qa.member_id, qq.quiz_id;

-- Update existing answers to reference their corresponding attempt
UPDATE quiz_answers qa
JOIN quiz_questions qq ON qa.question_id = qq.id
JOIN quiz_attempts qat ON qa.member_id = qat.member_id AND qq.quiz_id = qat.quiz_id
SET qa.attempt_id = qat.id
WHERE qa.attempt_id IS NULL;

-- Now make attempt_id NOT NULL since all existing answers have been migrated
ALTER TABLE `quiz_answers` MODIFY COLUMN `attempt_id` int(10) unsigned NOT NULL;
