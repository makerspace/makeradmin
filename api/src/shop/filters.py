from datetime import timedelta, date
from typing import TYPE_CHECKING, Any, Callable, Dict
from membership.models import Member
from shop.stripe_subscriptions import SubscriptionType
from service.db import db_session
from membership.membership import get_membership_summary
from service.error import BadRequest

if TYPE_CHECKING:
    from shop.transactions import CartItem


def filter_start_package(cart_item: "CartItem", member_id: int) -> None:
    end_date = get_membership_summary(member_id).labaccess_end

    if not end_date:
        return

    if date.today() < end_date + timedelta(days=30 * 9):
        raise BadRequest(
            "Starterpack can only be bought if you haven't had lab acccess during the last 9 months (30*9 days)."
        )

    if cart_item.count > 1:
        raise BadRequest("You may only buy a single Starterpack.")


def filter_no_subscription_active(
    sub: SubscriptionType,
) -> Callable[["CartItem", int], None]:
    def filter(cart_item: "CartItem", member_id: int) -> None:
        member: Member = db_session.query(Member).get(member_id)
        if sub == SubscriptionType.LAB:
            if member.stripe_labaccess_subscription_id is not None:
                raise BadRequest(
                    "You already have a makerspace access subscription. You must cancel your subscription if you want to buy invidual makerspace access months."
                )
        elif sub == SubscriptionType.MEMBERSHIP:
            if member.stripe_membership_subscription_id is not None:
                raise BadRequest(
                    "You already have a base membership subscription. You must cancel your subscription if you want to buy invidual base membership years."
                )
        else:
            assert False

    return filter


PRODUCT_FILTERS: Dict[str, Callable[["CartItem", int], None]] = {
    "start_package": filter_start_package,
    "labaccess_non_subscription_purchase": filter_no_subscription_active(SubscriptionType.LAB),
    "membership_non_subscription_purchase": filter_no_subscription_active(SubscriptionType.MEMBERSHIP),
}
