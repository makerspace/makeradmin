from dateutil import parser
from datetime import datetime, timedelta

from membership.membership import get_membership_summary
from service.error import BadRequest


def filter_start_package(cart_item, member_id):
    membership = get_membership_summary(member_id)
    
    end_date_str = membership['labaccess_end']
    
    if not end_date_str:
        return

    end_date = parser.parse(end_date_str)

    if end_date < datetime.now() + timedelta(days=30 * 9):
        raise BadRequest("Starterpack can only be bought if you haven't had"
                         " lab acccess during the last 9 months (30*9 days).")

    if cart_item.count > 1:
        raise BadRequest("Bad item count in starterpack, should be 1.")


PRODUCT_FILTERS = {
    "start_package": filter_start_package,
}
