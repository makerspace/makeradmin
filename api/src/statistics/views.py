from datetime import date, datetime
from statistics import service
from statistics.maker_statistics import (
    RetentionGraph,
    RetentionTable,
    ShopStatistics,
    lasertime,
    membership_by_date_statistics,
    membership_number_months2_default,
    membership_number_months_default,
    retention_graph,
    retention_table,
    shop_statistics,
)
from statistics.members_of_interest import members_of_interest
from statistics.physical_access_log import TimeGrouping, activity_by_date, activity_by_day_of_week
from typing import Any, Dict, List, Optional, Tuple

from flask import request
from membership.models import Span
from service.api_definition import GET, MEMBER_VIEW, PUBLIC
from service.error import BadRequest


@service.route("/membership/distribution_by_month2", method=GET, permission=PUBLIC)
def membership_number_months_default_route2():
    return membership_number_months2_default()


@service.route("/membership/distribution_by_month", method=GET, permission=PUBLIC)
def membership_number_months_default_route():
    return membership_number_months_default()


@service.route("/membership/by_date", method=GET, permission=PUBLIC)
def membership_by_date_statistics_route():
    return membership_by_date_statistics()


@service.route("/lasertime/by_month", method=GET, permission=PUBLIC)
def lasertime_route() -> List[Tuple[str, int]]:
    return lasertime()


@service.route("/shop/statistics", method=GET, permission=PUBLIC)
def shop_route() -> ShopStatistics:
    return shop_statistics()


def parse_limits() -> Tuple[Optional[datetime], Optional[datetime]]:
    return parse_date("start"), parse_date("end")


@service.route("/retention_graph", method=GET, permission=PUBLIC)
def retention_graph_route() -> RetentionGraph:
    return retention_graph(date(2020, 1, 1), date(2030, 12, 31))


@service.route("/retention/<spantype>", method=GET, permission=MEMBER_VIEW)
def retention_table_route(spantype: Span.ACCESS_TYPE) -> RetentionTable:
    start, end = parse_limits()
    return retention_table(start, end, spantype=spantype)


@service.route("/members_of_interest", method=GET, permission=MEMBER_VIEW)
def members_of_interest_route() -> Dict[str, Any]:
    start, end = parse_limits()
    return members_of_interest(start, end).to_dict()


def parse_date(param: str) -> Optional[datetime]:
    start_str = request.args.get(param, default=None)
    try:
        return datetime.fromisoformat(start_str) if start_str is not None else None
    except ValueError:
        raise BadRequest(
            f"Invalid query parameter {param}: '{start_str}'. Expected ISO date/datetime format. E.g YYYY-MM-DD"
        )


@service.route("/physical_access_log/activity/by_<grouping_str>", method=GET, permission=MEMBER_VIEW)
def activity_by_date_route(grouping_str: str) -> Dict[Any, Any]:
    start, end = parse_limits()
    try:
        grouping = TimeGrouping(grouping_str)
    except ValueError:
        raise BadRequest(f"Invalid grouping: {grouping_str}")

    return activity_by_date(start, end, grouping).to_dict()


@service.route(
    "/physical_access_log/activity/by_<grouping_str>/member/<int:member_id>", method=GET, permission=MEMBER_VIEW
)
def activity_by_date_member_route(grouping_str: str, member_id: int) -> Dict[Any, Any]:
    start, end = parse_limits()
    try:
        grouping = TimeGrouping(grouping_str)
    except ValueError:
        raise BadRequest(f"Invalid grouping: {grouping_str}")

    return activity_by_date(start, end, grouping, member_id=member_id).to_dict()


@service.route("/physical_access_log/activity/by_day_of_week", method=GET, permission=MEMBER_VIEW)
def activity_by_day_of_week_route() -> Dict[Any, Any]:
    start, end = parse_limits()
    return activity_by_day_of_week(start, end).to_dict()


@service.route(
    "/physical_access_log/activity/by_day_of_week/member/<int:member_id>", method=GET, permission=MEMBER_VIEW
)
def activity_by_day_of_week_member_route(member_id: int) -> Dict[Any, Any]:
    start, end = parse_limits()
    return activity_by_day_of_week(start, end, member_id=member_id).to_dict()
