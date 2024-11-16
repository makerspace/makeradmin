ALTER TABLE `quiz_questions` ADD COLUMN `mode` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
UPDATE `quiz_questions` SET `mode`='single_choice';
ALTER TABLE `quiz_questions` MODIFY COLUMN `mode` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL;
