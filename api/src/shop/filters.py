from datetime import timedelta, date

from membership.membership import get_membership_summary
from service.error import BadRequest


def filter_start_package(cart_item, member_id):
    end_date = get_membership_summary(member_id).labaccess_end
    
    if not end_date:
        return

    if date.today() < end_date + timedelta(days=30 * 9):
        raise BadRequest("Starterpack can only be bought if you haven't had"
                         " lab acccess during the last 9 months (30*9 days).")

    if cart_item['count'] > 1:
        raise BadRequest("You may only buy a single Starterpack.")


PRODUCT_FILTERS = {
    "start_package": filter_start_package,
}
