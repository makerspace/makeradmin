from datetime import date
from statistics import service
from statistics.maker_statistics import (
    RetentionGraph,
    lasertime,
    membership_by_date_statistics,
    membership_number_months2_default,
    membership_number_months_default,
    retention_graph,
    shop_statistics,
)

from service.api_definition import GET, PUBLIC


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
def lasertime_route():
    return lasertime()


@service.route("/shop/statistics", method=GET, permission=PUBLIC)
def shop_route():
    return shop_statistics()


@service.route("/retention_graph", method=GET, permission=PUBLIC)
def retention_graph_route() -> RetentionGraph:
    return retention_graph(date(2020, 1, 1), date(2030, 12, 31))
