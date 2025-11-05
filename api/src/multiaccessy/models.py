from datetime import datetime

from membership.models import Base, Member
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, configure_mappers, declarative_base, mapped_column, relationship


class PhysicalAccessEntry(Base):
    __tablename__ = "physical_access_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id: Mapped[int | None] = mapped_column(Integer, ForeignKey(Member.member_id), nullable=True)
    accessy_user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessy_asset_operation_id: Mapped[str] = mapped_column(Text, nullable=False)
    accessy_asset_publication_id: Mapped[str] = mapped_column(Text, nullable=False)
    invoked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
