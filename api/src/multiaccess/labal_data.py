# THIS FILE MIRRORS THE label_data.py FILE IN THE MEMBERBOOTH REPO
# TODO: Add a proper dependency and share this file

import json
import typing
from datetime import date, datetime, timedelta
from typing import Any, Literal, Type

import serde
from plum import dispatch
from serde import field


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


LabelType = TemporaryStorageLabel | BoxLabel | FireSafetyLabel | Printer3DLabel | NameTag | MeetupNameTag | DryingLabel
