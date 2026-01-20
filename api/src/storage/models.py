"""
Database models for generic file/image storage.
"""

from datetime import datetime
from typing import Optional

from membership.models import Base
from sqlalchemy import Index, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column


class Upload(Base):
    """Generic image/file storage table supporting multiple categories."""

    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    width: Mapped[Optional[int]] = mapped_column(default=None)
    height: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    __table_args__ = (Index("idx_category", "category", "deleted_at"),)

    def __repr__(self) -> str:
        return f"Upload(id={self.id}, category={self.category}, name={self.name})"
