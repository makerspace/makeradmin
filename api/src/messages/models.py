import enum

from membership.models import Member
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import configure_mappers, relationship

Base = declarative_base()


class MessageTemplate(enum.Enum):
    LABACCESS_REMINDER = "labaccess_reminder"
    LOGIN_LINK = "login_link"
    NEW_MEMBER = "new_member"
    RECEIPT = "receipt"
    PASSWORD_RESET = "password_reset"
    ADD_LABACCESS_TIME = "add_labaccess_time"
    ADD_MEMBERSHIP_TIME = "add_membership_time"
    BOX_WARNING = "box_warning"
    BOX_FINAL_WARNING = "box_final_warning"
    BOX_TERMINATED = "box_terminated"
    QUIZ_FIRST_NEWMEMBER = "quiz_first_newmember"
    QUIZ_FIRST_OLDMEMBER = "quiz_first_oldmember"
    QUIZ_REMINDER = "quiz_reminder"
    MEMBERSHIP_REMINDER = "membership_reminder"
    NEW_LOW_INCOME_MEMBER = "new_low_income_member"
    GIFT_CARD_PURCHASE = "gift_card_purchase"
    UPDATED_MEMBER_INFO = "updated_member_info"


class Message(Base):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"

    __tablename__ = "message"

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
        return f"Message(recipient_id={self.id}, subject={self.subject}, member_id={self.member_id})"


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
