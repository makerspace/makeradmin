from service.api_definition import GET, PUBLIC
from statistics import service
from statistics.maker_statistics import membership_by_date_statistics, lasertime


@service.route("/membership/by_date", method=GET, permission=PUBLIC)
def membership_by_date_statistics_route():
    return membership_by_date_statistics()


@service.route("/lasertime/by_month", method=GET, permission=PUBLIC)
def lasertime_route():
    return lasertime()


