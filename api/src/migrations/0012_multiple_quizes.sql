CREATE TABLE IF NOT EXISTS `quiz_quizzes` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `description` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `quiz_quizzes` (name, description) VALUES('Stockholm Makerspace Get Started Quiz!', "Hello and welcome as a member of Stockholm Makerspace! We are sure you are excited to get started on a project at the makerspace!\n\nTo help you get started we have put together this quiz as a learning tool. It will go through many common questions you might have and also many things that you might not have thought about but that are important for you to know in order to make Stockholm Makerspace work well.\n\nNote that this is not intended as a test of your knowledge, it is a way for new members to learn how things work without having to read through a long and boring document. Don't worry if you pick an incorrect answer, the questions you answered incorrectly will repeat until you have answered all of them correctly and are thus familiar with the basics of how things work at Stockholm Makerspace. Completing this quiz is a mandatory part of becoming a member. You will receive nagging emails every few days or so until you complete the quiz.");
ALTER TABLE `quiz_questions` ADD COLUMN `quiz_id` int unsigned NOT NULL;
UPDATE `quiz_questions` SET `quiz_id`=(SELECT id from quiz_quizzes WHERE name='Stockholm Makerspace Get Started Quiz!');
ALTER TABLE `quiz_questions` ADD CONSTRAINT `quiz_constraint` FOREIGN KEY (`quiz_id`) REFERENCES `quiz_quizzes` (`id`);
