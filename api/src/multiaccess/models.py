from datetime import datetime
from typing import Literal, Optional

import phonenumbers as phonenumbers
from membership.models import Member
from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MemberboothLabel(Base):
    __tablename__ = "memberbooth_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=False)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey(Member.member_id), nullable=False)

    # Serialized LabelType
    data: Mapped[JSON] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]

    member: Mapped[Member] = relationship(Member, backref="labels", cascade_backrefs=False)

    def __repr__(self) -> str:
        return f"MemberboothLabel(id={self.id} member_id={self.member_id})"


class MemberboothLabelAction(Base):
    __tablename__ = "memberbooth_labels_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    label_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(MemberboothLabel.id), nullable=False)
    action_member_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(Member.member_id), nullable=False)
    session_token: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    action: Mapped[Literal["observed", "reported", "cleaned_away"]] = mapped_column(
        Enum("observed", "reported", "cleaned_away", name="memberbooth_label_action_enum"), nullable=False
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image: Mapped[Optional[bytes]] = mapped_column("image", nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    label: Mapped[MemberboothLabel] = relationship("MemberboothLabel", backref="actions", foreign_keys=[label_id])
    action_member: Mapped[Member] = relationship(Member, backref="label_actions", foreign_keys=[action_member_id])

    def __repr__(self) -> str:
        return (
            f"MemberboothLabelAction(id={self.id}, label_id={self.label_id}, "
            f"action_member_id={self.action_member_id}, action={self.action})"
        )
