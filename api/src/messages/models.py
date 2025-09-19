import enum
from datetime import datetime
from typing import Literal, Optional

from membership.models import Member
from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, configure_mappers, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
    STATUS = Literal["queued", "sent", "failed"]
    QUEUED: STATUS = "queued"
    SENT: STATUS = "sent"
    FAILED: STATUS = "failed"

    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    member_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(Member.member_id))
    recipient_type: Mapped[Literal["email", "sms"]] = mapped_column(Enum("email", "sms"), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[STATUS] = mapped_column(Enum(QUEUED, SENT, FAILED), nullable=False)
    template: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # If this message was associated with some other object, this is the ID of that object
    # This can for example be the ID of a memberbooth label.
    # If the ID is used or not, and what it is, depends on the message template.
    associated_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    member: Mapped[Optional[Member]] = relationship(Member)

    def __repr__(self) -> str:
        return f"Message(id={self.id}, subject={self.subject}, member_id={self.member_id})"


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
