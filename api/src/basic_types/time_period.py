from datetime import datetime
from enum import Enum


class TimePeriod(Enum):
    Month = "month"
    Year = "year"
    Week = "week"
    Day = "day"


def date_to_period(date: datetime, period: TimePeriod) -> str:
    if period == TimePeriod.Month:
        return date.strftime("%Y-%m")
    elif period == TimePeriod.Year:
        return date.strftime("%Y")
    elif period == TimePeriod.Week:
        return date.strftime("%Y-%W")
    elif period == TimePeriod.Day:
        return date.strftime("%Y-%m-%d")
    else:
        raise ValueError(f"Unknown period {period}")
