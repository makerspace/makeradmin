import enum
from datetime import date, datetime
from typing import Any

from membership.models import Member
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime, Integer, Text


class Base(DeclarativeBase):
    pass


class Aggregation(enum.Enum):
    year = "year"
    month = "month"
    day = "day"


class AccountingExport(Base):
    __tablename__ = "webshop_accounting_exports"

    class Status(str, enum.Enum):
        completed = "completed"
        pending = "pending"
        failed = "failed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signer_member_id: Mapped[int] = mapped_column(Integer, ForeignKey(Member.member_id))
    content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[Status] = mapped_column(default=Status.pending)
    aggregation: Mapped[Aggregation] = mapped_column(default=Aggregation.month)
    start_date: Mapped[date]
    end_date: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[datetime | None]

    signer: Mapped[Member] = relationship()

    def __repr__(self) -> str:
        return f"AccountingFiles(id={self.id}, status={self.status}, start_date={self.start_date}, end_date={self.end_date}, aggregation={self.aggregation})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status.value,
            "aggregation": self.aggregation.value,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "signer_member_id": self.signer_member_id,
        }
