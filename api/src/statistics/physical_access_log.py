from dataclasses import dataclass, field
from datetime import date as datetime_date
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, List, Literal, Optional, Sequence, Tuple, cast

import sqlalchemy
from dataclasses_json import DataClassJsonMixin, config
from multiaccessy.models import PhysicalAccessEntry
from service.db import db_session
from service.logging import logger
from service.util import format_datetime
from sqlalchemy import ColumnElement, Date, distinct, func, select, text


@dataclass
class ActivityEntry(DataClassJsonMixin):
    date: datetime_date = field(metadata=config(encoder=format_datetime))
    count: int


@dataclass
class PhysicalActivity(DataClassJsonMixin):
    start_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))
    end_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))
    activity: List[ActivityEntry]


class TimeGrouping(Enum):
    Day = "day"
    Week = "week"
    Month = "month"
    Year = "year"


def activity_by_date(
    start: Optional[datetime], end: Optional[datetime], grouping: TimeGrouping, member_id: Optional[int] = None
) -> PhysicalActivity:
    if grouping == TimeGrouping.Day:
        selecter = func.date_format(PhysicalAccessEntry.invoked_at, "%Y-%m-%d").label("grouped_date")
    elif grouping == TimeGrouping.Year:
        selecter = func.date_format(PhysicalAccessEntry.invoked_at, "%Y-01-01").label("grouped_date")
    elif grouping == TimeGrouping.Month:
        selecter = func.date_format(PhysicalAccessEntry.invoked_at, "%Y-%m-01").label("grouped_date")
    elif grouping == TimeGrouping.Week:
        # Round down to the nearest Monday
        selecter = func.date_format(
            text("DATE_SUB(invoked_at, INTERVAL (DAYOFWEEK(invoked_at) - 1) DAY)"),
            "%Y-%m-%d",
        ).label("grouped_date")

    days: Sequence[Tuple[str, int]] = db_session.execute(
        select(
            selecter,
            func.count(distinct(PhysicalAccessEntry.member_id))
            if member_id is None
            else func.count(distinct(func.date_format(PhysicalAccessEntry.invoked_at, "%Y-%m-%d"))),
        )
        .where(
            PhysicalAccessEntry.invoked_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean)
        )
        .where(PhysicalAccessEntry.invoked_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .where(PhysicalAccessEntry.member_id.isnot(None))
        .where(
            PhysicalAccessEntry.member_id == member_id
            if member_id is not None
            else sqlalchemy.cast(True, sqlalchemy.Boolean)
        )
        .group_by("grouped_date")
        .order_by(selecter.asc())
    ).t.all()

    result: List[ActivityEntry] = []

    # Note: Will skip over days/weeks/months with no activity
    for day_str, count in days:
        day = datetime.strptime(day_str, "%Y-%m-%d").date()
        result.append(ActivityEntry(date=day, count=count))

    return PhysicalActivity(start_time=start, end_time=end, activity=result)


@dataclass
class ActivityByDayOfWeek(DataClassJsonMixin):
    week_starts_on: Literal["monday"]
    activity: List[List[int]]
    start_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))
    end_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))


def activity_by_day_of_week(
    start: Optional[datetime], end: Optional[datetime], member_id: Optional[int] = None
) -> ActivityByDayOfWeek:
    selecter = func.date_format(PhysicalAccessEntry.invoked_at, "%Y-%m-%d %H:00").label("grouped_date")
    activity_by_day = (
        select(selecter, func.count(distinct(PhysicalAccessEntry.member_id)).label("count"))
        .where(
            PhysicalAccessEntry.invoked_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean)
        )
        .where(PhysicalAccessEntry.invoked_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .where(PhysicalAccessEntry.member_id.isnot(None))
        .where(
            PhysicalAccessEntry.member_id == member_id
            if member_id is not None
            else sqlalchemy.cast(True, sqlalchemy.Boolean)
        )
        .group_by("grouped_date")
        .order_by(selecter.asc())
        .subquery()
    )

    activity_by_day_of_week: Sequence[Tuple[str, int]] = db_session.execute(
        select(
            func.date_format(activity_by_day.c.grouped_date, "%w %H").label("day_of_week"),
            func.sum(activity_by_day.c.count),
        )
        .group_by("day_of_week")
        .order_by("day_of_week")
    ).t.all()

    activity_by_day_and_hour = [[0 for _ in range(24)] for _ in range(7)]
    for day_of_week, count in activity_by_day_of_week:
        day, hour = map(int, day_of_week.split())
        day = (day - 1 + 7) % 7  # Ensure week starts on Monday
        assert activity_by_day_and_hour[day][hour] == 0
        activity_by_day_and_hour[day][hour] = int(count)

    return ActivityByDayOfWeek(
        week_starts_on="monday", activity=activity_by_day_and_hour, start_time=start, end_time=end
    )
