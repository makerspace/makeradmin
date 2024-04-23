from datetime import datetime
from enum import Enum

from zoneinfo import ZoneInfo


class TimePeriod(Enum):
    Month = "month"
    Year = "year"
    Week = "week"
    Day = "day"


def date_to_period(date: datetime, period: TimePeriod, zone_info: ZoneInfo = ZoneInfo("Europe/Stockholm")) -> str:
    if period == TimePeriod.Month:
        return date.astimezone(zone_info).strftime("%Y-%m")
    elif period == TimePeriod.Year:
        return date.astimezone(zone_info).strftime("%Y")
    elif period == TimePeriod.Week:
        return date.astimezone(zone_info).strftime("%Y-%W")
    elif period == TimePeriod.Day:
        return date.astimezone(zone_info).strftime("%Y-%m-%d")
    else:
        raise ValueError(f"Unknown period {period}")
