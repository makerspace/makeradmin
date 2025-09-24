# THIS FILE MIRRORS THE label_data.py FILE IN THE MEMBERBOOTH REPO
# TODO: Add a proper dependency and share this file

import json
import typing
from datetime import date, datetime, timedelta
from typing import Any, Literal, Type
from membership.models import Member
import serde
from plum import dispatch
from serde import field
from serde import InternalTagging
from service.db import db_session


class DateTimeSerializer:
    @dispatch
    def serialize(self, value: datetime) -> str:
        return datetime.isoformat(value, timespec="seconds")


class DateTimeDeserializer:
    @dispatch
    def deserialize(self, cls: Type[datetime], value: Any) -> datetime:
        return datetime.fromisoformat(value)


# Workaround for https://github.com/yukinarit/pyserde/issues/453
serde.add_serializer(DateTimeSerializer())
serde.add_deserializer(DateTimeDeserializer())


@serde.serde
class LabelBase:
    id: int
    created_by_member_number: int  # Can be different if a board member created the label for someone else
    member_number: int
    member_name: str
    created_at: datetime
    version: Literal[3]


@serde.serde
class TemporaryStorageLabel:
    base: LabelBase = field(flatten=True)
    description: str
    expires_at: date = field(serializer=date.isoformat, deserializer=date.fromisoformat)


@serde.serde
class BoxLabel:
    base: LabelBase = field(flatten=True)


@serde.serde
class FireSafetyLabel:
    base: LabelBase = field(flatten=True)
    expires_at: date = field(serializer=date.isoformat, deserializer=date.fromisoformat)


@serde.serde
class Printer3DLabel:
    base: LabelBase = field(flatten=True)


@serde.serde
class NameTag:
    base: LabelBase = field(flatten=True)
    membership_expires_at: date | None = field(serializer=date.isoformat, deserializer=date.fromisoformat)


@serde.serde
class MeetupNameTag:
    base: LabelBase = field(flatten=True)


@serde.serde
class DryingLabel:
    base: LabelBase = field(flatten=True)
    expires_at: datetime = field(serializer=datetime.isoformat, deserializer=datetime.fromisoformat)


@serde.serde(deny_unknown_fields=True)
class TemporaryStorageLabelV1:
    type: Literal["temp"]
    v: Literal[1]
    unix_timestamp: int
    member_number: int
    description: str
    expiry_date: date  # date in ISO format

    def migrate(self) -> TemporaryStorageLabel | None:
        member = db_session.query(Member).filter(Member.member_number == self.member_number, Member.deleted_at.is_(None)).first()
        if member is None:
            return None
        return TemporaryStorageLabel(
            base=LabelBase(
                id=self.unix_timestamp,
                created_by_member_number=self.member_number,
                member_number=self.member_number,
                member_name=f"{member.firstname} {member.lastname}",
                created_at=datetime.fromtimestamp(self.unix_timestamp),
                version=3,
            ),
            description=self.description,
            expires_at=self.expiry_date,
        )

@serde.serde(deny_unknown_fields=True)
class BoxLabelV2:
    type: Literal["box"]
    v: Literal[2]
    unix_timestamp: int
    member_number: int

    def migrate(self) -> BoxLabel | None:
        member = db_session.query(Member).filter(Member.member_number == self.member_number, Member.deleted_at.is_(None)).first()
        if member is None:
            return None
        return BoxLabel(
            base=LabelBase(
                id=self.unix_timestamp,
                created_by_member_number=self.member_number,
                member_number=self.member_number,
                member_name=f"{member.firstname} {member.lastname}",
                created_at=datetime.fromtimestamp(self.unix_timestamp),
                version=3,
            ),
        )

@serde.serde(deny_unknown_fields=True)
class BoxLabelV1:
    v: Literal[1]
    unix_timestamp: int
    member_number: int

    def migrate(self) -> BoxLabel:
        member = db_session.query(Member).filter(Member.member_number == self.member_number, Member.deleted_at.is_(None)).first()
        assert member is not None
        return BoxLabel(
            base=LabelBase(
                id=self.unix_timestamp,
                created_by_member_number=self.member_number,
                member_number=self.member_number,
                member_name=f"{member.firstname} {member.lastname}",
                created_at=datetime.fromtimestamp(self.unix_timestamp),
                version=3,
            ),
        )

LabelType = TemporaryStorageLabel | BoxLabel | FireSafetyLabel | Printer3DLabel | NameTag | MeetupNameTag | DryingLabel
LabelTypeTagged = InternalTagging("type", LabelType)