-- Migration: Image uploads for quiz feature
-- Creates generic uploads table for storing images inline in quiz descriptions and questions

-- Generic image storage table supporting multiple categories
CREATE TABLE uploads (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  category VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(64) NOT NULL,
  data MEDIUMBLOB NOT NULL,
  width INT UNSIGNED,
  height INT UNSIGNED,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME DEFAULT NULL,
  INDEX idx_category (category, deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
