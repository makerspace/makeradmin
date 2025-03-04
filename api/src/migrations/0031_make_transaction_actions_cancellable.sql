ALTER TABLE `webshop_transaction_actions` MODIFY COLUMN `status` ENUM('completed', 'pending', 'cancelled') NOT NULL DEFAULT 'pending';
