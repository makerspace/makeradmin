from membership.models import Member
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import configure_mappers, declarative_base, relationship

Base = declarative_base()


class PhysicalAccessEntry(Base):
    __tablename__ = "physical_access_log"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey(Member.member_id), nullable=True)
    accessy_user_id = Column(Text, nullable=True)
    accessy_asset_operation_id = Column(Text, nullable=False)
    accessy_asset_publication_id = Column(Text, nullable=False)
    invoked_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
