from logging import getLogger
from typing import Any, Optional

from membership.models import Member
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
    select,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import column_property, configure_mappers, relationship, validates

Base = declarative_base()


logger = getLogger("makeradmin")


class StorageMessageType(Base):
    __tablename__ = "storage_message_types"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    message_type = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"MessageType(id={self.id}, message_type={self.description})"  # TODO


class StorageType(Base):
    __tablename__ = "storage_types"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    storage_type = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, unique=True)
    has_fixed_end_date = Column(Boolean, nullable=False)
    number_of_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"StorageType(id={self.id}, storage_type={self.description})"  # TODO


class StorageItem(Base):
    __tablename__ = "storage_items"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey("membership_members.member_id"), nullable=False)
    members_description = Column(Text)
    item_label_id = Column(BigInteger, unique=True, nullable=False)
    last_check_at = Column(DateTime, nullable=True)
    fixed_end_date = Column(DateTime, nullable=True)
    storage_type_id = Column(Integer, ForeignKey("storage_types.id"), nullable=False)

    member = relationship(Member)
    storage_type = relationship(StorageType, backref="storage_items")

    def __repr__(self) -> str:
        return (
            f"Storage(id={self.id}, item_label_id={self.item_label_id}, member_id={self.member_id}"
            f", storage_type_id={self.storage_type_id}, last_check_at={self.last_check_at}, fixed_expire_date={self.fixed_end_date})"
        )


class StorageMessage(Base):
    __tablename__ = "storage_messages"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey("membership_members.member_id"), nullable=False)
    storage_item_id = Column(BigInteger, ForeignKey("storage_items.id"), nullable=False)
    message_type_id = Column(Integer, ForeignKey("storage_message_types.id"), nullable=False)
    message_at = Column(DateTime, server_default=func.now())

    member = relationship(Member)
    storage_type = relationship("StorageItem", backref="storage_messages")

    def __repr__(self) -> str:
        return (
            f"Message(id={self.id}, storage_item_id={self.storage_item_id}, member_id={self.member_id}"
            f", message_at={self.message_at}, message_type_id={self.message_type_id})"
        )


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
