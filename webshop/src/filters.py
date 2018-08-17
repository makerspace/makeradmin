from service import BackendException, APIGateway
from dateutil import parser
from datetime import datetime, timedelta
from webshop_entities import CartItem
from errors import InvalidItemCount


class CanNotBuyStartPackage(BackendException):
    def __init__(self):
        super().__init__(sv=f"Startpaket kan bara köpas om du inte har haft labaccess på 9 månader (30*9 dagar).",
                         en=f"Starterpack can only be bought if you haven't had lab acccess during the last 9 months (30*9 days).")


def filter_start_package(gateway: APIGateway, item: CartItem, member_id: int):
    member = gateway.get(f"membership/member/{member_id}/membership").json()

    if not member:
        return

    try:
        end_date_str = member['data']['labaccess_end']
    except KeyError as e:
        raise BackendException(f"Could not get member end_date, this is a bug: {e}")

    if not end_date_str:
        return

    try:
        end_date = parser.parse(end_date_str)

    except ValueError as e:
        raise BackendException(f"Could not parse member end_date, this is a bug: {e}")

    if end_date < datetime.now() + timedelta(days=30*9):
        raise CanNotBuyStartPackage()

    if item.count > 1:
        raise InvalidItemCount(item.name, 1, item.count)


product_filters = {
    "start_package": filter_start_package,
}
