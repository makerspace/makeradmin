from logging import getLogger
from typing import Any, Optional

import phonenumbers as phonenumbers
from basic_types.enums import PriceLevel
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


member_group = Table(
    "membership_members_groups",
    Base.metadata,
    Column("member_id", ForeignKey("membership_members.member_id"), primary_key=True),
    Column("group_id", ForeignKey("membership_groups.group_id"), primary_key=True),
)


class Member(Base):
    __tablename__ = "membership_members"

    member_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(60))
    firstname = Column(String(255), nullable=False)
    lastname = Column(String(255))
    civicregno = Column(String(25))
    company = Column(String(255))
    orgno = Column(String(12))
    address_street = Column(String(255))
    address_extra = Column(String(255))
    address_zipcode = Column(Integer)
    address_city = Column(String(255))
    address_country = Column(String(2))
    phone = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    # True during the registration flow as the payment is being processed
    pending_activation = Column(Boolean, nullable=False)

    member_number = Column(Integer, unique=True)
    labaccess_agreement_at = Column(DateTime)
    pin_code = Column(String(30))
    stripe_customer_id = Column(String(64))
    stripe_membership_subscription_id = Column(String(64))
    stripe_labaccess_subscription_id = Column(String(64))
    price_level = Column(Enum(*[x.value for x in PriceLevel]), nullable=False)
    price_level_motivation = Column(String)

    @validates("phone")
    def validate_phone(self, key: Any, value: Optional[str]) -> Optional[str]:
        return normalise_phone_number(value)

    groups = relationship("Group", secondary=member_group, back_populates="members")

    def __repr__(self) -> str:
        return f"Member(member_id={self.member_id}, member_number={self.member_number}, email={self.email})"


group_permission = Table(
    "membership_group_permissions",
    Base.metadata,
    Column("id", Integer, autoincrement=True, nullable=False, primary_key=True),
    Column("group_id", ForeignKey("membership_groups.group_id"), nullable=False),
    Column("permission_id", ForeignKey("membership_permissions.permission_id"), nullable=False),
)


class Group(Base):
    __tablename__ = "membership_groups"

    group_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    members = relationship("Member", secondary=member_group, lazy="dynamic", back_populates="groups")

    permissions = relationship("Permission", secondary=group_permission, back_populates="groups")

    def __repr__(self) -> str:
        return f"Group(group_id={self.group_id}, name={self.name})"


# Calculated property will be executed as a sub select for each groups, since it is not that many groups this will be
# fine.
Group.num_members = column_property(
    select([func.count(member_group.columns.member_id)])
    .where(Group.group_id == member_group.columns.group_id)
    .scalar_subquery()
)


class Permission(Base):
    __tablename__ = "membership_permissions"

    permission_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    permission = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    groups = relationship("Group", secondary=group_permission, back_populates="permissions")


class Key(Base):
    __tablename__ = "membership_keys"

    key_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey("membership_members.member_id"), nullable=False)
    description = Column(Text)
    tagid = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    member = relationship(Member, backref="keys")

    def __repr__(self) -> str:
        return f"Key(key_id={self.key_id}, tagid={self.tagid})"


class Span(Base):
    __tablename__ = "membership_spans"

    LABACCESS = "labaccess"
    MEMBERSHIP = "membership"
    SPECIAL_LABACESS = "special_labaccess"

    span_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey("membership_members.member_id"), nullable=False)
    startdate = Column(Date, nullable=False)  # Start date, inclusive
    enddate = Column(Date, nullable=False)  # End date, inclusive
    type = Column(Enum(LABACCESS, MEMBERSHIP, SPECIAL_LABACESS), nullable=False)
    creation_reason = Column(String(255), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    deletion_reason = Column(String(255))

    member = relationship(Member, backref="spans")

    def __repr__(self) -> str:
        return f"Span(span_id={self.span_id}, type={self.type}, enddate={self.enddate})"


class Box(Base):
    __tablename__ = "membership_box"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    member_id = Column(Integer, ForeignKey("membership_members.member_id"), nullable=False)

    # The id of the printed label on the box.
    box_label_id = Column(BigInteger, unique=True, nullable=False)

    # Scanning session to be able to make list of all scanned boxes during the session.
    session_token = Column(String(32), index=True, nullable=False)

    # Box last checked at timestamp.
    last_check_at = Column(DateTime, nullable=True)

    # Last time a nag mail was sent out for this box, note that for a member with several boxes this may not be the
    # last nag date for that member.
    last_nag_at = Column(DateTime, nullable=False)

    member = relationship(Member, backref="boxes")

    def __repr__(self) -> str:
        return (
            f"Box(id={self.id}, box_label_id={self.box_label_id}, member_id={self.member_id}"
            f", last_check_at={self.last_check_at}, last_nag_at={self.last_nag_at})"
        )


class PhoneNumberChangeRequest(Base):
    __tablename__ = "change_phone_number_requests"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey("membership_members.member_id"), nullable=True)
    phone = Column(String(255), nullable=False)

    # Number used to compare if the reques is valid or not.
    validation_code = Column(Integer, nullable=False)

    # If the request has been completed or not.
    completed = Column(Boolean, nullable=False)

    # When the request was made.
    timestamp = Column(DateTime, nullable=False)

    member = relationship(Member, backref="change_phone_number_requests")

    @validates("phone")
    def validate_phone(self, key: Any, value: Optional[str]) -> Optional[str]:
        return normalise_phone_number(value)

    def __repr__(self) -> str:
        return (
            f"ChangePhoneNumberRequest(id={self.id}, member_id={self.member_id}"
            f", completed={self.completed}, timestamp={self.timestamp})"
        )


def normalise_phone_number(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None

    try:
        p = phonenumbers.parse(phone, "SE")
    except phonenumbers.NumberParseException:
        raise ValueError(f"invalid phone number {phone[:40]}")

    if p.national_number in (112, 911, 1177, 11313, 116000, 11414, 90000):
        raise ValueError(f"not allowed phone number {phone[:40]}")

    return f"+{p.country_code}{p.national_number}"


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
