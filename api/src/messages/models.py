from sqlalchemy import Column, Integer, String, Text, DateTime, func, Date, ForeignKey, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, column_property

from membership.models import Member

Base = declarative_base()


class Message(Base):
    
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


class Recipient(Base):
    
    __tablename__ = 'messages_recipient'
    
    messages_recipient_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    messages_message_id = Column(Integer, ForeignKey(Message.messages_message_id), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    member_id = Column(Integer, ForeignKey(Member.member_id))
    recipient = Column(String(255))
    date_sent = Column(Date)
    status = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f'Recipient(recipient_id={self.messages_recipient_id}, title={self.title}, member_id={self.member_id})'


Message.num_recipients = column_property(select([func.count(Recipient.member_id)])
                                         .where(Message.messages_message_id == Recipient.messages_message_id))


class Template(Base):
    
    __tablename__ = 'messages_template'
    
    messages_template_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f'Template(template_id={self.messages_template_id}, name={self.name} title={self.title})'
