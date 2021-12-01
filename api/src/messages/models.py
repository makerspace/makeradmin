import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, func, Date, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, configure_mappers

from membership.models import Member

Base = declarative_base()


class MessageTemplate(enum.Enum):
    LABACCESS_REMINDER = 'labaccess_reminder'
    MEMBERSHIP_REMINDER = 'membership_reminder'
    LOGIN_LINK = 'login_link'
    NEW_MEMBER = 'new_member'
    RECEIPT = 'receipt'
    PASSWORD_RESET = 'password_reset'
    ADD_LABACCESS_TIME = 'add_labaccess_time'
    ADD_MEMBERSHIP_TIME = 'add_membership_time'
    BOX_WARNING = 'storage/box_warning'
    BOX_FINAL_WARNING = 'storage/box_final_warning'
    BOX_TERMINATED = 'storage/box_terminated'
    TEMP_STORAGE_WARNING_LAB = 'storage/temp_storage_warning_lab'
    TEMP_STORAGE_FINAL_WARNING_LAB = 'storage/temp_storage_final_warning_lab'
    TEMP_STORAGE_TERMINATED_LAB = 'storage/temp_storage_terminated_lab'
    TEMP_STORAGE_WARNING_DATE = 'storage/temp_storage_warning_date'
    TEMP_STORAGE_FINAL_WARNING_DATE = 'storage/temp_storage_final_warning_date'
    TEMP_STORAGE_TERMINATED_DATE = 'storage/temp_storage_terminated_date'
    TEMP_STORAGE_WARNING_BOTH = 'storage/temp_storage_warning_both'
    TEMP_STORAGE_FINAL_WARNING_BOTH = 'storage/temp_storage_final_warning_both'
    TEMP_STORAGE_TERMINATED_BOTH = 'storage/temp_storage_terminated_both'
    QUIZ_FIRST_NEWMEMBER = 'quiz/first_newmember'
    QUIZ_FIRST_OLDMEMBER = 'quiz/first_oldmember'
    QUIZ_REMINDER = 'quiz/reminder'


class Message(Base):
    
    QUEUED = 'queued'
    SENT = 'sent'
    FAILED = 'failed'
    
    __tablename__ = 'message'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    subject = Column(Text, nullable=False)
    body = Column(Text)
    member_id = Column(Integer, ForeignKey(Member.member_id))
    recipient = Column(String(255))
    status = Column(Enum(QUEUED, SENT, FAILED), nullable=False)
    template = Column(String(120), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    sent_at = Column(DateTime)

    member = relationship(Member)
    
    def __repr__(self):
        return f'Message(recipient_id={self.id}, subject={self.subject}, member_id={self.member_id})'


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
