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
    - The binding period is set by the `BINDING_PERIOD` constant.
    - Binding period prices need to be configured in the stripe dashboard with the metadata price_type=binding_period.
        - It should also be configured as recurring with the number of months that the binding period should be.
    - Currently the binding period need to have the same price per month as the non-binding period.
- Subscriptions will use the price that has the metadata price_type=recurring (except for the binding period).

Due to a limitation in how stripe works, we need to use a regular purchase for the first payment.
This is because stripe doesn't allow starting multiple subscriptions at the same time, which becomes a UX issue if the card requires 3D secure authentication
(we don't want the user to have to authenticate multiple times).
Therefore we use a regular purchase for the first payment, and then schedule the subscription to start at the next renewal date.
This logic is handled in the frontend.

"""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, cast
from sqlalchemy import func

import stripe

from datetime import datetime, timezone, date, time, timedelta
from stripe.error import InvalidRequestError
from shop.stripe_util import retry
from membership.enums import PriceLevel
from shop.stripe_discounts import get_discount_for_product, get_price_level_for_member
from shop.models import Product, ProductAction, ProductCategory
from service.error import BadRequest, NotFound
from service.db import db_session
from membership.models import Member
from membership.membership import get_membership_summary
from shop.stripe_constants import (
    STRIPE_CURRENTY_BASE,
    MakerspaceMetadataKeys as MSMetaKeys,
    PriceType,
    SubscriptionScheduleStatus,
    CURRENCY,
)
from shop.stripe_constants import SubscriptionStatus
import stripe.error


class SubscriptionType(str, Enum):
    MEMBERSHIP = "membership"
    LAB = "labaccess"


logger = getLogger("makeradmin")

# Binding period in months.
# Set to zero to disable binding periods.
# Setting it to 1 is not particularly useful, since it will be the same as a normal subscription.
BINDING_PERIOD = {
    SubscriptionType.MEMBERSHIP: 0,
    SubscriptionType.LAB: 2,
}


def setup_subscription_makeradmin_product(
    subscription_type: SubscriptionType,
) -> Product:
    # TODO: Maybe we should create separate products for the binding period.
    # This would allow us to have different prices for the binding period and the recurring period.
    # Not sure if that's useful though.

    name = f"{subscription_type.value.title()} Subscription"

    offset = 0
    while True:
        with db_session.begin_nested():
            try:
                offset += 1
                category = (
                    db_session.query(ProductCategory).filter(ProductCategory.name == "Subscriptions").one_or_none()
                )
                if category is None:
                    category = ProductCategory(
                        name="Subscriptions",
                        display_order=(db_session.query(func.max(ProductCategory.display_order)).scalar() or 0)
                        + offset,
                    )
                    db_session.add(category)
                    db_session.flush()

                break
            except Exception as e:
                # I think, if this setup happens inside a transaction, we may not be able to see another category with the same display order,
                # but we will still be prevented from creating a new one with that display order.
                # So we incrementally increase the display order until we find a free one.
                # This race condition will basically only happen when executing tests in parallel.
                # TODO: Can this be done in a better way?
                print("Race condition when creating category. Trying again: ", e)

    product: Optional[Product] = db_session.query(Product).filter(Product.name == name).one_or_none()
    new = False
    if product is None:
        new = True
        product = Product()

    product.name = name
    product.description = f"Stripe subscription for {subscription_type.value}"
    subscription_prices = lookup_subscription_price_for(subscription_type)
    recurring_price = subscription_prices.recurring_price
    product.category_id = category.id
    product.product_metadata = {
        MSMetaKeys.SUBSCRIPTION_TYPE.value: f"{subscription_type.value}",
        MSMetaKeys.SPECIAL_PRODUCT_ID.value: f"{subscription_type.value}_subscription",
        # Allow subscriptions to be discounted
        MSMetaKeys.ALLOWED_PRICE_LEVELS.value: [PriceLevel.LowIncomeDiscount.value],
    }
    interval = recurring_price["recurring"]["interval"]
    if interval == "month":
        product.unit = "mån"
        average_days = 30
    elif interval == "year":
        product.unit = "år"
        average_days = 365
    else:
        raise RuntimeError(f"Unexpected interval {interval} in stripe product")
    assert int(recurring_price["recurring"]["interval_count"]) == 1
    assert recurring_price["type"] == "recurring"
    assert recurring_price["currency"] == CURRENCY, f"Expected prices to be in currency: {CURRENCY}, not {recurring_price['currency']}"
    product.price = Decimal(recurring_price["unit_amount"]) / STRIPE_CURRENTY_BASE

    # The smallest_multiple field is somewhat like a binding period.
    # The frontend may use this to display binding period information for subscriptions.
    if subscription_prices.binding_period_price is not None:
        product.smallest_multiple = subscription_prices.binding_period_price["recurring"]["interval_count"]

        # Just a sanity check, but not actually a requirement.
        assert product.smallest_multiple >= 2, "Binding period must be at least 2 months"
    else:
        product.smallest_multiple = 1

    product.filter = ""
    product.show = False  # The subscription products are not shown in the shop
    if new:
        product.display_order = (db_session.query(func.max(Product.display_order)).scalar() or 0) + 1
        db_session.add(product)

    # Flush to be able to get the product id
    db_session.flush()

    # Delete all existing product actions for this product, and create new ones.
    # When a subscription runs as normal, these actions will not be triggered,
    # instead the paid invoice will be processed, and there's some custom code to add membership
    # for the exact number of days that stripe says that the invoice was for (it may vary depending on the number of days in a month for example).
    # However, when a member starts a new subscription, we will use a regular purchase for the first payment.
    # This purchase will use these actions. The stripe subscription will instead start on the renewal date.
    #
    # A regular purchase is used for the first payment, since otherwise it is not possible to start multiple subscriptions (or start one subscription and pay for something else)
    # at the same time, if the card requires 3D secure authentication.
    # This is an annoying stripe limitation.
    # By making the first payment a regular purchase, we can make sure the subscription is always scheduled for the future
    # instead of starting immediately.
    db_session.query(ProductAction).filter(ProductAction.product_id == product.id).delete()
    actions = {
        SubscriptionType.LAB: ProductAction.ADD_LABACCESS_DAYS,
        SubscriptionType.MEMBERSHIP: ProductAction.ADD_MEMBERSHIP_DAYS,
    }
    action = ProductAction(product_id=product.id, action_type=actions[subscription_type], value=average_days)
    db_session.add(action)

    db_session.flush()
    return product


SUBSCRIPTION_PRODUCTS: Optional[Dict[SubscriptionType, int]] = None


def get_subscription_products() -> Dict[SubscriptionType, int]:
    # Setup the products for the subscriptions lazily
    global SUBSCRIPTION_PRODUCTS
    if SUBSCRIPTION_PRODUCTS is None:
        SUBSCRIPTION_PRODUCTS = {
            SubscriptionType.MEMBERSHIP: setup_subscription_makeradmin_product(SubscriptionType.MEMBERSHIP).id,
            SubscriptionType.LAB: setup_subscription_makeradmin_product(SubscriptionType.LAB).id,
        }

    return SUBSCRIPTION_PRODUCTS


def get_subscription_product(subscription_type: SubscriptionType) -> Product:
    p_id = get_subscription_products()[subscription_type]
    p = db_session.query(Product).get(p_id)
    if p is None:
        # The product doesn't exist anymore.
        # When we are running tests, this can happen if the database is reset between tests.
        global SUBSCRIPTION_PRODUCTS
        SUBSCRIPTION_PRODUCTS = None
        return get_subscription_product(subscription_type)
    return p


def get_stripe_subscriptions(stripe_customer_id: str, active_only: bool = True) -> List[stripe.Subscription]:
    """Returns the list of subscription objects for the given user."""
    resp = retry(lambda: stripe.Subscription.list(customer=stripe_customer_id))
    return [
        sub
        for sub in resp["data"]
        if not active_only
        or SubscriptionStatus(sub["status"]) in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRAILING]
    ]


def delete_stripe_customer(member_id: int) -> None:
    member = db_session.query(Member).get(member_id)
    if member is None:
        raise NotFound(f"Unable to find member with id {member_id}")
    if member.stripe_customer_id is not None:
        # Note: This will also delete all subscriptions
        stripe.Customer.delete(member.stripe_customer_id)

    member.stripe_customer_id = None
    db_session.flush()


def attach_and_set_default_payment_method(
    member: Member,
    payment_method: stripe.PaymentMethod,
    test_clock: Optional[stripe.test_helpers.TestClock] = None,
) -> None:
    stripe_member = get_stripe_customer(member, test_clock=test_clock)
    assert stripe_member is not None
    stripe.PaymentMethod.attach(payment_method, customer=stripe_member.stripe_id)
    stripe.Customer.modify(
        stripe_member.stripe_id,
        invoice_settings={
            "default_payment_method": payment_method.stripe_id,
        },
    )


def are_metadata_dicts_equivalent(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    a = {k: v for k, v in a.items() if v != ""}
    b = {k: v for k, v in b.items() if v != ""}
    return a == b


def get_stripe_customer(
    member_info: Member, test_clock: Optional[stripe.test_helpers.TestClock]
) -> Optional[stripe.Customer]:
    # Stripe will reject emails with trailing whitespace
    member_email = member_info.email.strip()
    try:
        if member_info.stripe_customer_id is not None:
            try:
                customer = retry(lambda: stripe.Customer.retrieve(member_info.stripe_customer_id))
                assert customer is not None

                # Update the metadata if needed
                expected_metadata = {
                    # Setting to an empty string will delete the key if present
                    MSMetaKeys.PENDING_MEMBER.value: "pending" if member_info.pending_activation else "",
                    MSMetaKeys.USER_ID.value: member_info.member_id,
                    MSMetaKeys.MEMBER_NUMBER.value: member_info.member_number,
                }
                if (
                    not are_metadata_dicts_equivalent(customer.metadata, expected_metadata)
                    or customer.email != member_email
                ):
                    stripe.Customer.modify(
                        customer["id"],
                        description=f"Created by Makeradmin (#{member_info.member_number})",
                        email=member_email,
                        name=f"{member_info.firstname} {member_info.lastname}",
                        metadata=expected_metadata,
                    )
                return customer
            except InvalidRequestError as e:
                if "No such customer" in str(e.user_message):
                    print("Stripe customer not found, even though it existed in the database. Creating a new one.")

        # If no customer is found, we create one
        customer = retry(
            lambda: stripe.Customer.create(
                description=f"Created by Makeradmin (#{member_info.member_number})",
                email=member_email,
                name=f"{member_info.firstname} {member_info.lastname}",
                metadata={
                    MSMetaKeys.USER_ID.value: member_info.member_id,
                    MSMetaKeys.MEMBER_NUMBER.value: member_info.member_number,
                },
                test_clock=test_clock,
            )
        )

        # Note: Stripe doesn't update its search index of customers immediately,
        # so the new customer may not be visible to stripe.Customer.search for a few seconds.
        # Therefore we always try to find the customer by its ID, that we store in the database
        member_info.stripe_customer_id = customer.stripe_id
        db_session.flush()
        return customer
    except Exception as e:
        print(f"Unable to get or create stripe user: {e}")

    return None


@dataclass
class ProductPricing:
    recurring_price: stripe.Price
    binding_period_price: Optional[stripe.Price]


K = TypeVar("K")
V = TypeVar("V")


class Cache(Generic[K, V]):
    data: Dict[K, Tuple[datetime, V]] = dict()
    ttl: timedelta

    def __init__(self, ttl: timedelta):
        self.ttl = ttl

    def get(self, key: K) -> Optional[V]:
        if key not in self.data:
            return None
        if self.data[key][0] < datetime.now():
            del self.data[key]
            return None
        return self.data[key][1]

    def set(self, key: K, value: V) -> None:
        self.data[key] = (datetime.now() + self.ttl, value)


# Cache the subscription prices for an hour to avoid hitting the stripe API too often
SUBSCRIPTION_PRICE_CACHE = Cache[SubscriptionType, ProductPricing](timedelta(hours=1))


def lookup_subscription_price_for(
    subscription_type: SubscriptionType,
) -> ProductPricing:
    res = SUBSCRIPTION_PRICE_CACHE.get(subscription_type)
    if res is not None:
        return res

    products = retry(
        lambda: stripe.Product.search(
            query=f"metadata['{MSMetaKeys.SUBSCRIPTION_TYPE.value}']:'{subscription_type.value}'"
        )
    )
    assert (
        len(products.data) == 1
    ), f"Expected to find a single stripe product with metadata->{MSMetaKeys.SUBSCRIPTION_TYPE.value}={subscription_type.value}, but found {len(products.data)}"
    product = products.data[0]

    prices = list(retry(lambda: stripe.Price.list(product=product.stripe_id)))

    # Don't include archived prices
    prices = [p for p in prices if p["active"]]

    recurring_prices = [
        p
        for p in prices
        if MSMetaKeys.PRICE_TYPE.value in p["metadata"]
        if p["metadata"][MSMetaKeys.PRICE_TYPE.value] == PriceType.RECURRING.value
    ]
    assert (
        len(recurring_prices) == 1
    ), f"Expected to find a single stripe price for {subscription_type.name} with metadata->{MSMetaKeys.PRICE_TYPE.value}={PriceType.RECURRING.value}, but found {len(recurring_prices)} prices: {[p.stripe_id for p in recurring_prices]}"
    recurring_price = recurring_prices[0]

    if BINDING_PERIOD[subscription_type] > 0:
        binding_period = BINDING_PERIOD[subscription_type]
        # Filter by metadata
        starting_prices = [
            p
            for p in prices
            if MSMetaKeys.PRICE_TYPE.value in p["metadata"]
            if p["metadata"][MSMetaKeys.PRICE_TYPE.value] == PriceType.BINDING_PERIOD.value
        ]
        # Filter by period
        starting_prices = [
            p
            for p in starting_prices
            if p["recurring"]["interval"] == "month" and p["recurring"]["interval_count"] == binding_period
        ]

        assert (
            len(starting_prices) == 1
        ), f"Expected to find a single stripe price for {subscription_type.name} with metadata->{MSMetaKeys.PRICE_TYPE.value}={PriceType.BINDING_PERIOD.value}, a period of exactly {binding_period} months, but found {len(starting_prices)} prices: {[p.stripe_id for p in starting_prices]}"
        binding_period_price = starting_prices[0]
    else:
        binding_period_price = None

    res = ProductPricing(recurring_price=recurring_price, binding_period_price=binding_period_price)
    SUBSCRIPTION_PRICE_CACHE.set(subscription_type, res)
    return res


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


def start_subscription(
    member_id: int,
    subscription_type: SubscriptionType,
    test_clock: Optional[stripe.test_helpers.TestClock],
    earliest_start_at: Optional[datetime] = None,
    expected_to_pay_now: Optional[Decimal] = None,
    expected_to_pay_recurring: Optional[Decimal] = None,
) -> str:
    try:
        print(f"Attempting to start new subscription {subscription_type}")

        (was_already_member, subscription_start) = calc_subscription_start_time(
            member_id, subscription_type, earliest_start_at
        )

        member = db_session.query(Member).get(member_id)
        assert member is not None
        stripe_customer = get_stripe_customer(member, test_clock)
        if stripe_customer is None:
            raise BadRequest(f"Unable to find corresponding stripe member {member}")
        assert member.stripe_customer_id == stripe_customer.stripe_id

        price = lookup_subscription_price_for(subscription_type)

        discount = get_discount_for_product(
            get_subscription_product(subscription_type),
            get_price_level_for_member(member),
        )

        # Check that the price is as expected
        # This is done to ensure that the frontend logic is in sync with the backend logic and the user
        # has been presented the correct price before starting the subscription.
        if expected_to_pay_now is not None:
            if was_already_member:
                # If the member already has the relevant membership, the subscription will start at the end of the current period, and nothing is paid right now
                to_pay_now = Decimal(0)
            else:
                # Fetch a fresh price object from stripe to make sure we have the latest price
                to_pay_now_price = stripe.Price.retrieve(
                    (price.binding_period_price or price.recurring_price).stripe_id
                )
                to_pay_now = (
                    (Decimal(to_pay_now_price["unit_amount"]) / STRIPE_CURRENTY_BASE) * (1 - discount.fraction_off)
                ).quantize(Decimal("0.01"))
            if to_pay_now != expected_to_pay_now:
                raise BadRequest(
                    f"Expected to pay {expected_to_pay_now} now, for starting {subscription_type} subscription, but should actually pay {to_pay_now}"
                )

        if expected_to_pay_recurring is not None:
            # Fetch a fresh price object from stripe to make sure we have the latest price
            to_pay_recurring_price = stripe.Price.retrieve(price.recurring_price.stripe_id)
            to_pay_recurring = (
                (Decimal(to_pay_recurring_price["unit_amount"]) / STRIPE_CURRENTY_BASE) * (1 - discount.fraction_off)
            ).quantize(Decimal("0.01"))
            if to_pay_recurring != expected_to_pay_recurring:
                raise BadRequest(
                    f"Expected to pay {expected_to_pay_recurring} when {subscription_type} subscription renews, but the recurring price is {to_pay_recurring}"
                )

        if subscription_type == SubscriptionType.MEMBERSHIP:
            current_subscription_id = member.stripe_membership_subscription_id
        elif subscription_type == SubscriptionType.LAB:
            current_subscription_id = member.stripe_labaccess_subscription_id
        else:
            assert False

        if current_subscription_id is not None:
            if current_subscription_id.startswith("sub_sched_"):
                current_subscription = stripe.SubscriptionSchedule.retrieve(current_subscription_id)
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
                    cancel_subscription(member_id, subscription_type, test_clock)
                except Exception as e:
                    print(type(e))
                    print(e)
                    raise e

        metadata = {
            MSMetaKeys.USER_ID.value: member_id,
            MSMetaKeys.MEMBER_NUMBER.value: member.member_number,
            MSMetaKeys.SUBSCRIPTION_TYPE.value: subscription_type.value,
        }

        phases = []
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
        if price.binding_period_price is not None and not was_already_member:
            phases.append(
                {
                    "items": [
                        {
                            "price": price.binding_period_price.stripe_id,
                            "metadata": metadata,
                        },
                    ],
                    "collection_method": "charge_automatically",
                    "metadata": metadata,
                    "proration_behavior": "none",
                    "iterations": 1,
                    "coupon": discount.coupon.stripe_id if discount.coupon is not None else None,
                }
            )

        phases.append(
            {
                "items": [
                    {
                        "price": price.recurring_price.stripe_id,
                        "metadata": metadata,
                    },
                ],
                "collection_method": "charge_automatically",
                "metadata": metadata,
                "proration_behavior": "none",
                "coupon": discount.coupon.stripe_id if discount.coupon is not None else None,
            }
        )

        subscription_schedule = stripe.SubscriptionSchedule.create(
            start_date=int(subscription_start.timestamp()),
            customer=stripe_customer.stripe_id,
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
    member_id: int,
    subscription_type: SubscriptionType,
    earliest_start_at: Optional[datetime],
    test_clock: Optional[stripe.test_helpers.TestClock],
) -> bool:
    member: Optional[Member] = db_session.query(Member).get(member_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {member_id}")

    if subscription_type == SubscriptionType.MEMBERSHIP:
        subscription_id = member.stripe_membership_subscription_id
    elif subscription_type == SubscriptionType.LAB:
        subscription_id = member.stripe_labaccess_subscription_id
    else:
        assert False

    if subscription_id is None:
        return False

    if subscription_id.startswith("sub_sched_"):
        # The subscription is scheduled for the future.
        # We can just wait for it to start as normal
        return False

    subscription = stripe.Subscription.retrieve(subscription_id)
    # If the subscription is not paused, we can just do nothing.
    if subscription["pause_collection"] is None:
        return False

    # Resuming stripe subscriptions is possible,
    # but it was very tricky to do it while handling binding periods correctly.
    # So we just cancel the subscription and start a new one.
    # Much less code, much lower risk of bugs. Everyone is happy :)
    cancel_subscription(member_id, subscription_type, test_clock)
    start_subscription(member_id, subscription_type, test_clock, earliest_start_at)
    return True


def pause_subscription(
    member_id: int,
    subscription_type: SubscriptionType,
    test_clock: Optional[stripe.test_helpers.TestClock],
) -> bool:
    member: Optional[Member] = db_session.query(Member).get(member_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {member_id}")
    stripe_customer = get_stripe_customer(member, test_clock)
    assert stripe_customer is not None
    assert member.stripe_customer_id == stripe_customer.stripe_id

    if subscription_type == SubscriptionType.MEMBERSHIP:
        subscription_id = member.stripe_membership_subscription_id
    elif subscription_type == SubscriptionType.LAB:
        subscription_id = member.stripe_labaccess_subscription_id
    else:
        assert False

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
            stripe.Subscription.modify(
                sid=subscription_id,
                pause_collection={
                    "behavior": "void",
                    "resumes_at": None,
                },
            )
            return True
        else:
            assert False
    except stripe.error.InvalidRequestError as e:
        if e.code == "resource_missing":
            # The subscription was already deleted
            # We might have missed the webhook to delete the reference from the member.
            # Or the webhook might be on its way.
            return False
        else:
            raise


def cancel_subscription(
    member_id: int,
    subscription_type: SubscriptionType,
    test_clock: Optional[stripe.test_helpers.TestClock],
) -> bool:
    member: Optional[Member] = db_session.query(Member).get(member_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {member_id}")
    stripe_customer = get_stripe_customer(member, test_clock)
    assert stripe_customer is not None
    assert member.stripe_customer_id == stripe_customer.stripe_id

    if subscription_type == SubscriptionType.MEMBERSHIP:
        subscription_id = member.stripe_membership_subscription_id
    elif subscription_type == SubscriptionType.LAB:
        subscription_id = member.stripe_labaccess_subscription_id
    else:
        assert False

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
                stripe.SubscriptionSchedule.release(subscription_id)

                if schedule["subscription"]:
                    # Also delete the subscription which the schedule drives, if one exists
                    stripe.Subscription.delete(sid=schedule["subscription"])

        elif subscription_id.startswith("sub_"):
            stripe.Subscription.delete(sid=subscription_id)
        else:
            assert False
    except stripe.error.InvalidRequestError as e:
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


def open_stripe_customer_portal(member_id: int, test_clock: Optional[stripe.test_helpers.TestClock]) -> str:
    """Create a customer portal session and return the URL to which the user should be redirected."""
    member = db_session.query(Member).get(member_id)
    assert member is not None
    stripe_customer = get_stripe_customer(member, test_clock)
    assert stripe_customer is not None

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
    except stripe.error.InvalidRequestError as e:
        if e.code == "invoice_upcoming_none":
            return SubscriptionInfo(
                type=sub_type,
                active=False,
                upcoming_invoice=None,
            )
        else:
            raise e


def list_subscriptions(member_id: int) -> List[SubscriptionInfo]:
    member = db_session.query(Member).get(member_id)
    assert member is not None

    stripe_customer = get_stripe_customer(member, test_clock=None)
    assert stripe_customer is not None

    result: List[SubscriptionInfo] = []
    for sub_type, sub_id in [
        (SubscriptionType.LAB, member.stripe_labaccess_subscription_id),
        (SubscriptionType.MEMBERSHIP, member.stripe_membership_subscription_id),
    ]:
        if sub_id is not None:
            if sub_id.startswith("sub_sched_"):
                sched = stripe.SubscriptionSchedule.retrieve(sub_id)
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
