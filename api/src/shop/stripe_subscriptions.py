"""
This module contains the logic for handling Stripe subscriptions.

The model for subscriptions is as follows:
- A member may have at most one membership subscription and at most one makespace access subscription.
- A subscription is a Stripe subscription.
- When subscription is created, we look at the current membership of the member and may schedule the subscription to start in the future instead of immediately.
- The member stores the Stripe subscription id, or the schedule id in the database (the schedule if the subscription is scheduled to start in the future).
- When subscriptions are paid, a transaction is added to makeradmin with an action that indicates that days should be added to their membership.
    - The order is shipped immediately.
- When a new member starts subscribing to makerspace membership, and they haven't signed the access agreement, we pause the subscription immediately after the first payment.
    - This is done since the member will not be able to get any makespace access until after they sign the makespace access agreement.
    - When the lab membership agreement is signed (and orders are shipped), we resume the subscription.
- Subscriptions may have binding periods. This means that the member will pay for N months in advance the first time they pay, and then the normal subscription will continue.
    - The binding period is set by the smallest multiple in the makeradmin product that corresponds to the subsscription.
    - Currently the binding period need to have the same price per month as the non-binding period.
- Subscriptions will use the price from the makeradmin product
- Subscriptions use custom product actions via transaction actions instead of the product action associated with the subscription product. This is because the number of days in a month varies.

Due to a limitation in how stripe works, we need to use a regular purchase for the first payment.
This is because stripe doesn't allow starting multiple subscriptions at the same time, which becomes a UX issue if the card requires 3D secure authentication
(we don't want the user to have to authenticate multiple times).
Therefore we use a regular purchase for the first payment, and then schedule the subscription to start at the next renewal date.
This logic is handled in the frontend.

"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, cast

import stripe
from basic_types.enums import PriceLevel
from membership.membership import get_membership_summary
from membership.models import Member
from service.db import db_session
from service.error import BadRequest, InternalServerError, NotFound
from sqlalchemy import func
from stripe import InvalidRequestError

from shop.models import Product, ProductAction, ProductCategory
from shop.stripe_constants import (
    CURRENCY,
    STRIPE_CURRENTY_BASE,
    PriceType,
    SubscriptionScheduleStatus,
    SubscriptionStatus,
)
from shop.stripe_constants import MakerspaceMetadataKeys as MSMetaKeys
from shop.stripe_customer import get_and_sync_stripe_customer
from shop.stripe_discounts import get_discount_for_product, get_price_level_for_member
from shop.stripe_product_price import get_and_sync_stripe_product_and_prices
from shop.stripe_util import are_metadata_dicts_equivalent, convert_from_stripe_amount, retry


class SubscriptionType(str, Enum):
    MEMBERSHIP = "membership"
    LAB = "labaccess"


logger = getLogger("makeradmin")


SUBSCRIPTION_PRODUCTS: Optional[Dict[SubscriptionType, int]] = None


def get_subscription_id(member: Member, subscription_type: SubscriptionType) -> str | None:
    if subscription_type == SubscriptionType.MEMBERSHIP:
        return member.stripe_membership_subscription_id
    elif subscription_type == SubscriptionType.LAB:
        return member.stripe_labaccess_subscription_id
    else:
        raise InternalServerError(f"Unknown SubscriptionType {subscription_type}")


def get_stripe_subscriptions(stripe_customer_id: str, active_only: bool = True) -> List[stripe.Subscription]:
    """Returns the list of subscription objects for the given user."""
    resp = retry(lambda: list(stripe.Subscription.list(customer=stripe_customer_id).auto_paging_iter()))
    return [
        sub
        for sub in resp
        if not active_only
        or SubscriptionStatus(sub["status"]) in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRAILING]
    ]


def calc_start_ts(current_end_date: date, now: datetime) -> datetime:
    end_dt = datetime.combine(current_end_date, time(0, 0, 0, tzinfo=timezone.utc))

    # If the trial lasts for more than a day, we reduce the period by a day to
    # make sure we start billing the customer in time.
    return max(now, end_dt - timedelta(days=1))


def calc_subscription_start_time(
    member_id: int,
    subscription_type: SubscriptionType,
    earliest_start_at: Optional[datetime],
) -> Tuple[bool, datetime]:
    if earliest_start_at is None:
        earliest_start_at = datetime.now(timezone.utc)
    assert earliest_start_at.tzinfo is not None, "earliest_start_at must be timezone aware"

    memberships = get_membership_summary(member_id, earliest_start_at)
    was_already_member = False
    if memberships.membership_active and subscription_type == SubscriptionType.MEMBERSHIP:
        assert memberships.membership_end is not None
        subscription_start = calc_start_ts(memberships.membership_end, earliest_start_at)
        was_already_member = True
    elif memberships.labaccess_active and subscription_type == SubscriptionType.LAB:
        assert memberships.labaccess_end is not None
        subscription_start = calc_start_ts(memberships.labaccess_end, earliest_start_at)
        was_already_member = True
    else:
        subscription_start = earliest_start_at

    return was_already_member, subscription_start


def get_makeradmin_subscription_product(subscription_type: SubscriptionType) -> Product:
    # Import here to prevent circular imports
    from shop.shop_data import get_product_data_by_special_id

    special_id = f"{subscription_type.value}_subscription"
    product = get_product_data_by_special_id(special_id)
    if product is None:
        raise InternalServerError(
            f"Unable to find product for subscription_type {subscription_type.value} with special id {special_id}"
        )
    return product


def start_subscription(
    member: Member,
    subscription_type: SubscriptionType,
    earliest_start_at: Optional[datetime] = None,
    expected_to_pay_now: Optional[Decimal] = None,
    expected_to_pay_recurring: Optional[Decimal] = None,
    test_clock: Optional[stripe.test_helpers.TestClock] = None,
) -> str:
    stripe_customer = get_and_sync_stripe_customer(member, test_clock)
    if stripe_customer is None:
        raise BadRequest(f"Unable to create, find or update corresponding stripe customer for member {member}")

    if stripe_customer.invoice_settings is None or not stripe_customer.invoice_settings["default_payment_method"]:
        raise BadRequest(message="You must add a default payment method before starting a subscription.")

    logger.info(f"Attempting to start new subscription {subscription_type}")
    try:
        (was_already_member, subscription_start) = calc_subscription_start_time(
            member.member_id, subscription_type, earliest_start_at
        )

        makeradmin_subscription_product = get_makeradmin_subscription_product(subscription_type)

        discount = get_discount_for_product(
            makeradmin_subscription_product,
            get_price_level_for_member(member),
        )
        # Sync stripe products and prices to ensure everything is up to date
        stripe_product, stripe_prices = get_and_sync_stripe_product_and_prices(makeradmin_subscription_product)

        metadata = {
            MSMetaKeys.USER_ID.value: str(member.member_id),
            MSMetaKeys.MEMBER_NUMBER.value: str(member.member_number),
            MSMetaKeys.SUBSCRIPTION_TYPE.value: subscription_type.value,
        }

        phases: List[stripe.SubscriptionSchedule.CreateParamsPhase] = []
        # If the user is not already a member, we require a binding period.
        # This allows someone to switch to a subscription without a binding period
        # if they have been paying as they go for individual months (or if they just cancelled a subscription)
        # If we raise the binding time to more than two months we may want to
        # do something fancier here. As otherwise a user could just buy 1 month
        # of membership, and then switch to a subscription which might normally
        # have, say, a 6 month binding period.
        # But with the current binding period of 2 months, this is not a problem.
        # And we might not even want to change it even if we increase the binding period.
        # The binding period is primarily to prevent people from subscribing and then
        # immediately cancelling.
        #
        # Note: This case typically does not happen, because in the frontend
        # we convert all subscription starts to direct payments, if the user is not already a member.
        # This allows us to start multiple subscriptions with the same transaction, since stripe
        # is terrible and will otherwise need multiple 3d-secure authentication iterations.
        # Thus when we reach this point, we will basically always already have access (was_already_member=True).
        # This code will trigger during some tests, however.
        if PriceType.BINDING_PERIOD in stripe_prices and not was_already_member:
            phase: stripe.SubscriptionSchedule.CreateParamsPhase = {
                "items": [
                    {
                        "price": stripe_prices[PriceType.BINDING_PERIOD].id,
                        "metadata": metadata,
                    },
                ],
                "collection_method": "charge_automatically",
                "metadata": metadata,
                "proration_behavior": "none",
                "iterations": 1,
            }
            if discount.coupon is not None:
                phase["coupon"] = discount.coupon.id
            phases.append(phase)

        phase = {
            "items": [
                {
                    "price": stripe_prices[PriceType.RECURRING].id,
                    "metadata": metadata,
                },
            ],
            "collection_method": "charge_automatically",
            "metadata": metadata,
            "proration_behavior": "none",
        }
        if discount.coupon is not None:
            phase["coupon"] = discount.coupon.id
        phases.append(phase)

        # Check that the price is as expected
        # This is done to ensure that the frontend logic is in sync with the backend logic and the user
        # has been presented the correct price before starting the subscription.
        if expected_to_pay_now is not None:
            if was_already_member:
                # If the member already has the relevant membership, the subscription will start at the end of the current period, and nothing is paid right now
                to_pay_now = Decimal(0)
            else:
                to_pay_now_price = (
                    stripe_prices[PriceType.BINDING_PERIOD]
                    if PriceType.BINDING_PERIOD in stripe_prices
                    else stripe_prices[PriceType.RECURRING]
                )
                assert phases[0]["items"][0]["price"] == to_pay_now_price.id
                assert to_pay_now_price.unit_amount is not None
                to_pay_now = convert_from_stripe_amount(to_pay_now_price.unit_amount) * (1 - discount.fraction_off)
            if to_pay_now != expected_to_pay_now:
                raise BadRequest(
                    f"Expected to pay {expected_to_pay_now} now, for starting {subscription_type} subscription, but should actually pay {to_pay_now}"
                )

        if expected_to_pay_recurring is not None:
            to_pay_recurring_price = stripe_prices[PriceType.RECURRING]
            assert phases[-1]["items"][0]["price"] == to_pay_recurring_price.id
            assert to_pay_recurring_price.unit_amount is not None
            to_pay_recurring = convert_from_stripe_amount(to_pay_recurring_price.unit_amount) * (
                1 - discount.fraction_off
            )
            if to_pay_recurring != expected_to_pay_recurring:
                raise BadRequest(
                    f"Expected to pay {expected_to_pay_recurring} when {subscription_type} subscription renews, but the recurring price is {to_pay_recurring}"
                )

        current_subscription_id = get_subscription_id(member, subscription_type)
        if current_subscription_id is not None:
            if current_subscription_id.startswith("sub_sched_"):
                current_subscription: stripe.SubscriptionSchedule | stripe.Subscription = (
                    stripe.SubscriptionSchedule.retrieve(current_subscription_id)
                )
            else:
                current_subscription = stripe.Subscription.retrieve(current_subscription_id)

            if current_subscription is None:
                # Possibly the subscription has been deleted, but the webhook hasn't been processed yet.
                pass
            else:
                # If the current subscription is still active, we cancel it and start a new one.
                # The UI should ideally prevent us from doing this, but it's better to be safe than sorry.
                # The subscription could also be trailing. In that the user has already cancelled it,
                # but it has not yet been deleted. In that case the cancel is a NOOP.
                try:
                    cancel_subscription(member, subscription_type, test_clock)
                except Exception as e:
                    print(type(e))
                    print(e)
                    raise e

        subscription_schedule = stripe.SubscriptionSchedule.create(
            start_date=int(subscription_start.timestamp()),
            customer=member.stripe_customer_id,
            metadata=metadata,
            phases=phases,
        )

        schedule_id: str = subscription_schedule["id"]

        # The subscription schedule will have a null subscription until it is started.
        # So we use the subscription schedule id temporarily.

        if subscription_type == SubscriptionType.MEMBERSHIP:
            member.stripe_membership_subscription_id = schedule_id
        elif subscription_type == SubscriptionType.LAB:
            member.stripe_labaccess_subscription_id = schedule_id
        else:
            assert False

        db_session.flush()
        return schedule_id
    except Exception as e:
        raise BadRequest("Internal error: " + str(e))


def resume_paused_subscription(
    member: Member,
    subscription_type: SubscriptionType,
    earliest_start_at: Optional[datetime],
    test_clock: Optional[stripe.test_helpers.TestClock] = None,
) -> bool:
    stripe_customer = get_and_sync_stripe_customer(member, test_clock)
    if stripe_customer is None:
        raise BadRequest(f"Unable to create, find or update corresponding stripe customer for member {member}")

    subscription_id = get_subscription_id(member, subscription_type)
    if subscription_id is None:
        return False

    if subscription_id.startswith("sub_sched_"):
        # The subscription is scheduled for the future.
        # We can just wait for it to start as normal
        return False

    subscription = retry(lambda: stripe.Subscription.retrieve(subscription_id))
    # If the subscription is not paused, we can just do nothing.
    if subscription["pause_collection"] is None:
        return False

    # Resuming stripe subscriptions is possible,
    # but it was very tricky to do it while handling binding periods correctly.
    # So we just cancel the subscription and start a new one.
    # Much less code, much lower risk of bugs. Everyone is happy :)
    cancel_subscription(member, subscription_type, test_clock=test_clock)
    start_subscription(member, subscription_type, earliest_start_at, test_clock=test_clock)
    return True


def pause_subscription(
    member: Member,
    subscription_type: SubscriptionType,
    test_clock: Optional[stripe.test_helpers.TestClock] = None,
) -> bool:
    stripe_customer = get_and_sync_stripe_customer(member, test_clock)
    if stripe_customer is None:
        raise BadRequest(f"Unable to create, find or update corresponding stripe customer for member {member}")

    subscription_id = get_subscription_id(member, subscription_type)
    if subscription_id is None:
        return False

    try:
        # The subscription might be a scheduled one so we need to check the id prefix
        # to determine which API to use.
        if subscription_id.startswith("sub_sched_"):
            # A subscription schedule cannot be paused.
            # Fortunately, we should never have to do this.
            # Subscriptions are paused when a new member signs up,
            # but hasn't yet signed the membership agreement.
            # But subscription schedules are only used for members
            # that already had membership when they signed up for the subscription.
            return False
        elif subscription_id.startswith("sub_"):
            retry(
                lambda: stripe.Subscription.modify(
                    subscription_id,
                    pause_collection={"behavior": "void"},
                )
            )
            return True
        else:
            assert False
    except stripe.InvalidRequestError as e:
        if e.code == "resource_missing":
            # The subscription was already deleted
            # We might have missed the webhook to delete the reference from the member.
            # Or the webhook might be on its way.
            return False
        else:
            raise


def cancel_subscription(
    member: Member,
    subscription_type: SubscriptionType,
    test_clock: Optional[stripe.test_helpers.TestClock] = None,
) -> bool:
    stripe_customer = get_and_sync_stripe_customer(member, test_clock)
    if stripe_customer is None:
        raise BadRequest(f"Unable to create, find or update corresponding stripe customer for member {member}")

    subscription_id = get_subscription_id(member, subscription_type)
    if subscription_id is None:
        return False

    try:
        # The subscription might be a scheduled one so we need to check the id prefix
        # to determine which API to use.

        # We delete the subscription here. This will make stripe send us an event
        # and that will make us remove the reference from the member.
        # We rely on webhooks as much as possible since this allows admins to
        # manage subscriptions and customers from the stripe dashboard without
        # the risk of getting out of sync with the database.
        if subscription_id.startswith("sub_sched_"):
            schedule = stripe.SubscriptionSchedule.retrieve(subscription_id)
            if SubscriptionScheduleStatus(schedule.status) in [
                SubscriptionScheduleStatus.NOT_STARTED,
                SubscriptionScheduleStatus.ACTIVE,
            ]:
                retry(lambda: stripe.SubscriptionSchedule.release(subscription_id))

                if schedule["subscription"]:
                    # Also delete the subscription which the schedule drives, if one exists
                    retry(lambda: stripe.Subscription.delete(schedule["subscription"]))

        elif subscription_id.startswith("sub_"):
            # (mypy falsely doesn't use the class-method of the delete method)
            retry(lambda: stripe.Subscription.delete(subscription_id))  # type: ignore[arg-type]
        else:
            assert False
    except stripe.InvalidRequestError as e:
        if e.code == "resource_missing":
            # The subscription was already deleted.
            # We might have missed the webhook to delete the reference from the member.
            # Or the webhook might be on its way.
            # Since it is a risk that we have missed it, we should remove the reference from the member here.
            if subscription_type == SubscriptionType.MEMBERSHIP:
                member.stripe_membership_subscription_id = None
            elif subscription_type == SubscriptionType.LAB:
                member.stripe_labaccess_subscription_id = None
            else:
                assert False
            db_session.flush()
        else:
            raise

    return True


def open_stripe_customer_portal(member_id: int) -> str:
    """Create a customer portal session and return the URL to which the user should be redirected."""
    member = db_session.query(Member).get(member_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {member_id}")

    stripe_customer = get_and_sync_stripe_customer(member)
    if stripe_customer is None:
        raise BadRequest(f"Unable to find corresponding stripe member {member}")

    billing_portal_session = stripe.billing_portal.Session.create(customer=stripe_customer["id"])
    print(billing_portal_session)

    return cast(str, billing_portal_session.url)


@dataclass
class UpcomingInvoice:
    payment_date: datetime
    amount_due: Decimal


@dataclass
class SubscriptionInfo:
    type: SubscriptionType
    active: bool
    upcoming_invoice: Optional[UpcomingInvoice]


def get_subscription_info_from_subscription(sub_type: SubscriptionType, sub_id: str) -> SubscriptionInfo:
    try:
        if sub_id.startswith("sub_sched_"):
            upcoming = stripe.Invoice.upcoming(schedule=sub_id)
        else:
            upcoming = stripe.Invoice.upcoming(subscription=sub_id)

        return SubscriptionInfo(
            type=sub_type,
            active=True,
            upcoming_invoice=UpcomingInvoice(
                payment_date=datetime.fromtimestamp(upcoming["next_payment_attempt"], tz=timezone.utc),
                amount_due=Decimal(upcoming["amount_due"]) / STRIPE_CURRENTY_BASE,
            ),
        )
    except stripe.InvalidRequestError as e:
        if e.code == "invoice_upcoming_none" or e.code == "resource_missing":
            # Seems like our data is inaccurate. The subscription is not active.
            return SubscriptionInfo(
                type=sub_type,
                active=False,
                upcoming_invoice=None,
            )
        else:
            print(e.code)
            raise e


def list_subscriptions(member_id: int) -> List[SubscriptionInfo]:
    member = db_session.query(Member).get(member_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {member_id}")

    stripe_customer = get_and_sync_stripe_customer(member, test_clock=None)
    if stripe_customer is None:
        raise BadRequest(f"Unable to find corresponding stripe member {member}")

    result: List[SubscriptionInfo] = []
    for sub_type, sub_id in [
        (SubscriptionType.LAB, member.stripe_labaccess_subscription_id),
        (SubscriptionType.MEMBERSHIP, member.stripe_membership_subscription_id),
    ]:
        if sub_id is not None:
            if sub_id.startswith("sub_sched_"):
                sched = retry(lambda: stripe.SubscriptionSchedule.retrieve(sub_id))
                status = SubscriptionScheduleStatus(sched.status)
                if status == SubscriptionScheduleStatus.NOT_STARTED:
                    # The subscription is scheduled to start at some point in the future.
                    # This most likely means the member already had some membership when they signed up for the subscription.
                    # We don't want to start the subscription until the member actually needs it.
                    result.append(get_subscription_info_from_subscription(sub_type, sub_id))
                elif status == SubscriptionScheduleStatus.ACTIVE:
                    # We may just be waiting for the webhook to fire. So generally we should not be in this state for more than a few seconds.
                    # Though in dev mode, the webhook may not fire at all if the developer hasn't configured stripe events properly (see readme).
                    print(
                        "If the subscription schedule has started, the member should have a reference to the started subscription instead."
                    )
                    result.append(get_subscription_info_from_subscription(sub_type, sub_id))
                elif status in [
                    SubscriptionScheduleStatus.RELEASED,
                    SubscriptionScheduleStatus.COMPLETED,
                    SubscriptionScheduleStatus.CANCELED,
                ]:
                    result.append(
                        SubscriptionInfo(
                            type=sub_type,
                            active=False,
                            upcoming_invoice=None,
                        )
                    )
                else:
                    assert False, f"Unexpected subscription schedule status {status}"
            else:
                result.append(get_subscription_info_from_subscription(sub_type, sub_id))
        else:
            result.append(
                SubscriptionInfo(
                    type=sub_type,
                    active=False,
                    upcoming_invoice=None,
                )
            )

    return result
