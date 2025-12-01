-- Create member_preferences table
CREATE TABLE member_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT UNSIGNED NOT NULL,
    question_type ENUM('ROOM_PREFERENCE', 'MACHINE_PREFERENCE') NOT NULL,
    available_options TEXT NOT NULL,
    selected_options TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (member_id) REFERENCES membership_members(member_id),
    INDEX idx_member_question (member_id, question_type)
);
