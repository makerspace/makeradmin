from datetime import datetime
from logging import getLogger
from typing import Any, List, Literal, Optional

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
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    column_property,
    configure_mappers,
    mapped_column,
    relationship,
    validates,
)


class Base(DeclarativeBase):
    pass


logger = getLogger("makeradmin")

member_group = Table(
    "membership_members_groups",
    Base.metadata,
    Column("member_id", ForeignKey("membership_members.member_id"), primary_key=True),
    Column("group_id", ForeignKey("membership_groups.group_id"), primary_key=True),
)


class Member(Base):
    __tablename__ = "membership_members"

    member_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(60))
    firstname: Mapped[str] = mapped_column(String(255), nullable=False)
    lastname: Mapped[Optional[str]] = mapped_column(String(255))
    civicregno: Mapped[Optional[str]] = mapped_column(String(25))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    orgno: Mapped[Optional[str]] = mapped_column(String(12))
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_extra: Mapped[Optional[str]] = mapped_column(String(255))
    address_zipcode: Mapped[Optional[int]]
    address_city: Mapped[Optional[str]] = mapped_column(String(255))
    address_country: Mapped[Optional[str]] = mapped_column(String(2))
    phone: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]

    # True during the registration flow as the payment is being processed
    pending_activation: Mapped[bool]

    member_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    labaccess_agreement_at: Mapped[Optional[datetime]]
    pin_code: Mapped[Optional[str]]
    stripe_customer_id: Mapped[Optional[str]]
    stripe_membership_subscription_id: Mapped[Optional[str]]
    stripe_labaccess_subscription_id: Mapped[Optional[str]]
    price_level: Mapped[str] = mapped_column(Enum(*[x.value for x in PriceLevel]), nullable=False)
    price_level_motivation: Mapped[Optional[str]]

    @validates("phone")
    def validate_phone(self, key: Any, value: Optional[str]) -> Optional[str]:
        return normalise_phone_number(value)

    groups: Mapped[List["Group"]] = relationship(
        "Group", secondary=member_group, back_populates="members", cascade_backrefs=False
    )

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

    group_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]

    members: Mapped[List[Member]] = relationship(
        "Member", secondary=member_group, lazy="dynamic", back_populates="groups", cascade_backrefs=False
    )

    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary=group_permission, back_populates="groups", cascade_backrefs=False
    )

    def __repr__(self) -> str:
        return f"Group(group_id={self.group_id}, name={self.name})"


# Calculated property will be executed as a sub select for each groups, since it is not that many groups this will be
# fine.
Group.num_members = column_property(
    select(func.count(member_group.columns.member_id))
    .where(Group.group_id == member_group.columns.group_id)
    .scalar_subquery()
)


class Permission(Base):
    __tablename__ = "membership_permissions"

    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    permission: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]

    groups: Mapped[List[Group]] = relationship(
        "Group", secondary=group_permission, back_populates="permissions", cascade_backrefs=False
    )


class Key(Base):
    __tablename__ = "membership_keys"

    key_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("membership_members.member_id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tagid: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]

    member: Mapped[Member] = relationship(Member, backref="keys", cascade_backrefs=False)

    def __repr__(self) -> str:
        return f"Key(key_id={self.key_id}, tagid={self.tagid})"


class Span(Base):
    __tablename__ = "membership_spans"

    ACCESS_TYPE = Literal["labaccess", "membership", "special_labaccess"]
    LABACCESS: ACCESS_TYPE = "labaccess"
    MEMBERSHIP: ACCESS_TYPE = "membership"
    SPECIAL_LABACESS: ACCESS_TYPE = "special_labaccess"

    span_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("membership_members.member_id"), nullable=False)
    startdate: Mapped[Date] = mapped_column(Date, nullable=False)  # Start date, inclusive
    enddate: Mapped[Date] = mapped_column(Date, nullable=False)  # End date, inclusive
    type: Mapped[ACCESS_TYPE] = mapped_column(Enum(LABACCESS, MEMBERSHIP, SPECIAL_LABACESS), nullable=False)
    creation_reason: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]
    deletion_reason: Mapped[Optional[str]]

    member: Mapped[Member] = relationship(Member, backref="spans", cascade_backrefs=False)

    def __repr__(self) -> str:
        return f"Span(span_id={self.span_id}, type={self.type}, enddate={self.enddate})"


class Box(Base):
    __tablename__ = "membership_box"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)

    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("membership_members.member_id"), nullable=False)

    # The id of the printed label on the box.
    box_label_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    # Scanning session to be able to make list of all scanned boxes during the session.
    session_token: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # Box last checked at timestamp.
    last_check_at: Mapped[Optional[datetime]]

    # Last time a nag mail was sent out for this box, note that for a member with several boxes this may not be the
    # last nag date for that member.
    last_nag_at: Mapped[Optional[datetime]]

    member: Mapped[Member] = relationship(Member, backref="boxes", cascade_backrefs=False)

    def __repr__(self) -> str:
        return (
            f"Box(id={self.id}, box_label_id={self.box_label_id}, member_id={self.member_id}"
            f", last_check_at={self.last_check_at}, last_nag_at={self.last_nag_at})"
        )


class PhoneNumberChangeRequest(Base):
    __tablename__ = "change_phone_number_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("membership_members.member_id"), nullable=True)
    phone: Mapped[str] = mapped_column(String(255), nullable=False)

    # Number used to compare if the reques is valid or not.
    validation_code: Mapped[int]

    # If the request has been completed or not.
    completed: Mapped[bool]

    # When the request was made.
    timestamp: Mapped[datetime]

    member: Mapped[Member] = relationship(Member, backref="change_phone_number_requests", cascade_backrefs=False)

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
