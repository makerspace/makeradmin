-- Create global settings table for system-wide configuration
-- Simple key-value store; all metadata (types, descriptions, permissions) defined in code
CREATE TABLE `core_settings` (
    `key` VARCHAR(255) PRIMARY KEY NOT NULL,
    `value` TEXT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
