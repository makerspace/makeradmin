from service.api_definition import GET, PUBLIC
from statistics import service


@service.route("/membership/by_date", method=GET, permission=PUBLIC)
def membership_by_date_statistics():
    return {
        "membership": spans_by_date("membership"),
        "labaccess": spans_by_date("labaccess"),
    }


