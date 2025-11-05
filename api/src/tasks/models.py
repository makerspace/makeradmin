from datetime import datetime
from typing import Literal, Optional

from membership.models import Base, Member
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class TaskDelegationLog(Base):
    __tablename__ = "task_delegation_log"
    ACTION_TYPE = Literal[
        "assigned",
        "completed",
        "not_done_did_something_else",
        "not_done_confused",
        "not_done_forgot",
        "not_done_no_time",
        "not_done_other",
        "ignored",
    ]

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("membership_members.member_id"), nullable=True
    )  # Member ID, can be null if the task just needed to be marked as done, without having a member associated
    card_id: Mapped[str] = mapped_column(String(128), nullable=False)  # Trello card ID
    card_name: Mapped[str | None] = mapped_column(Text, nullable=True)  # Trello card name
    action: Mapped["TaskDelegationLog.ACTION_TYPE"] = mapped_column(
        Enum(
            "assigned",
            "completed",
            "not_done_did_something_else",
            "not_done_confused",
            "not_done_forgot",
            "not_done_no_time",
            "not_done_other",
            "ignored",
            name="task_action",
        ),
        nullable=False,
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    member: Mapped[Optional[Member]] = relationship(Member, cascade_backrefs=False)


class TaskDelegationLogLabel(Base):
    __tablename__ = "task_delegation_log_labels"

    log_id: Mapped[int] = mapped_column(ForeignKey("task_delegation_log.id"), primary_key=True, nullable=False)
    label: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)

    log: Mapped[TaskDelegationLog] = relationship("TaskDelegationLog", backref="labels", cascade_backrefs=False)
