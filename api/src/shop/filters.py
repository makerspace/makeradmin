from datetime import timedelta, date
from typing import Any, Callable, Dict
from membership.models import Member
from shop.stripe_checkout import SubscriptionType
from service.db import db_session
from membership.membership import get_membership_summary
from service.error import BadRequest


def filter_start_package(cart_item: Dict[str, Any], member_id: int) -> None:
    end_date = get_membership_summary(member_id).labaccess_end

    if not end_date:
        return

    if date.today() < end_date + timedelta(days=30 * 9):
        raise BadRequest(
            "Starterpack can only be bought if you haven't had"
            " lab acccess during the last 9 months (30*9 days)."
        )

    if cart_item["count"] > 1:
        raise BadRequest("You may only buy a single Starterpack.")


def filter_no_subscription_active(
    sub: SubscriptionType,
) -> Callable[[Dict[str, Any], int], None]:
    def filter(cart_item: Dict[str, Any], member_id: int) -> None:
        member: Member = db_session.query(Member).find(member_id).one()
        if sub == SubscriptionType.LAB:
            if member.stripe_labaccess_subscription_id is not None:
                raise BadRequest(
                    "You already have a labaccess subscription. Please change to the pay-as-you-go plan before purchasing individual labaccess months"
                )
        elif sub == SubscriptionType.MEMBERSHIP:
            if member.stripe_membership_subscription_id is not None:
                raise BadRequest(
                    "You already have an association subscription. You cannot buy invidual association membership years."
                )
        else:
            assert False

    return filter


PRODUCT_FILTERS: Dict[str, Callable[[Dict[str, Any], int], None]] = {
    "start_package": filter_start_package,
    "labaccess_non_subscription_purchase": filter_no_subscription_active(
        SubscriptionType.LAB
    ),
    "membership_non_subscription_purchase": filter_no_subscription_active(
        SubscriptionType.MEMBERSHIP
    ),
}
