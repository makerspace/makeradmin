from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Message(Base):
    # CREATE TABLE IF NOT EXISTS `messages_message` (
    #   `messages_message_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    #   `title` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
    #   `description` text COLLATE utf8mb4_0900_ai_ci,
    #   `message_type` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
    #   `status` varchar(255) COLLATE utf8mb4_0900_ai_ci NOT NULL,
    #   `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #   `updated_at` datetime DEFAULT NULL,
    #   PRIMARY KEY (`messages_message_id`)
    # ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    
    __tablename__ = 'messages_message'
    
    messages_message_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    message_type = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f'Message(message_id={self.messages_message_id}, title={self.title}, status={self.status})'

# Calculated property will be executed as a sub select for each groups, since it is not that many groups this will be
# fine.
# TODO Add calculated property
Message.num_recipients = None #column_property(select([func.count(member_group.columns.member_id)]) .where(Group.group_id == member_group.columns.group_id))
