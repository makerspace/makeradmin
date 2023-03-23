from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast
from time import sleep
from sqlalchemy import func

import stripe

from datetime import datetime, timezone, date, time, timedelta
from stripe.error import InvalidRequestError, CardError, StripeError
from shop.models import Product, ProductAction, ProductCategory
from service.error import BadRequest, InternalServerError, EXCEPTION
from service.db import db_session
from membership.models import Member
from membership.membership import get_membership_summary
from shop.stripe_constants import MakerspaceMetadataKeys as MSMetaKeys, PriceType
from shop.stripe_constants import SubscriptionStatus
import stripe.error

# print(f"Stripe api_key={stripe.api_key}")

# stripe.api_key = 'sk_test_4QHS9UR02FMGKPqdjElznDRI'


class SubscriptionType(Enum):
    MEMBERSHIP = "membership"
    LAB = "labaccess"


logger = getLogger("makeradmin")


def setup_subscription_makeradmin_products(
    subscription_type: SubscriptionType,
) -> Product:
    name = f"{subscription_type.value.title()} Subscription"

    category = (
        db_session.query(ProductCategory)
        .filter(ProductCategory.name == "Subscriptions")
        .one_or_none()
    )
    if category is None:
        category = ProductCategory(
            name="Subscriptions",
            display_order=(
                db_session.query(func.max(ProductCategory.display_order)).scalar() or 0
            )
            + 1,
        )
        db_session.add(category)
        db_session.flush()

    product: Optional[Product] = (
        db_session.query(Product).filter(Product.name == name).one_or_none()
    )
    new = False
    if product is None:
        new = True
        product = Product()

    product.name = name
    product.description = f"Stripe subscription for {subscription_type.value}"
    stripe_price = lookup_subscription_price_for(
        None, subscription_type
    ).recurring_price
    price = stripe.Price.retrieve(stripe_price)
    product.category_id = category.id
    product.unit = price["recurring"]["interval"]
    assert int(price["recurring"]["interval_count"]) == 1
    assert price["type"] == "recurring"
    assert price["currency"] == "sek"
    product.price = Decimal(price["unit_amount"]) / 100
    product.smallest_multiple = 1
    product.filter = ""
    product.show = False  # The subscription products are not shown in the shop
    if new:
        product.display_order = (
            db_session.query(func.max(Product.display_order)).scalar() or 0
        ) + 1
        db_session.add(product)

    db_session.commit()
    return product


SUBSCRIPTION_PRODUCTS: Optional[Dict[SubscriptionType, int]] = None


def get_subscription_products() -> Dict[SubscriptionType, int]:
    # Setup the products for the subscriptions lazily
    global SUBSCRIPTION_PRODUCTS
    if SUBSCRIPTION_PRODUCTS is None:
        SUBSCRIPTION_PRODUCTS = {
            SubscriptionType.MEMBERSHIP: setup_subscription_makeradmin_products(
                SubscriptionType.MEMBERSHIP
            ).id,
            SubscriptionType.LAB: setup_subscription_makeradmin_products(
                SubscriptionType.LAB
            ).id,
        }

    return SUBSCRIPTION_PRODUCTS


def get_subscription_product(subscription_type: SubscriptionType) -> Product:
    p = db_session.query(Product).get(get_subscription_products()[subscription_type])
    if p is None:
        # The product doesn't exist anymore.
        # Possibly a new test has been started and the database has been reset.
        global SUBSCRIPTION_PRODUCTS
        SUBSCRIPTION_PRODUCTS = None
        return get_subscription_product(subscription_type)
    return p


def get_stripe_subscriptions(
    stripe_customer_id: str, active_only: bool = True
) -> List[stripe.Subscription]:
    """Returns the list of subscription objects for the given user."""
    resp = stripe.Subscription.list(customer=stripe_customer_id)
    return [
        sub
        for sub in resp["data"]
        if not active_only
        or SubscriptionStatus(sub["status"])
        in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRAILING]
    ]


def delete_stripe_customer(member_id: int) -> None:
    member: Member = db_session.query(Member).get(member_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {member_id}")
    if member.stripe_customer_id is not None:
        # Note: This will also delete all subscriptions
        stripe.Customer.delete(member.stripe_customer_id)

    member.stripe_customer_id = None
    db_session.commit()


def get_stripe_customer(
    member_info: Member, test_clock: Optional[stripe.test_helpers.TestClock]
) -> Optional[stripe.Customer]:
    try:
        if member_info.stripe_customer_id is not None:
            try:
                customer = stripe.Customer.retrieve(member_info.stripe_customer_id)
                assert customer is not None

                # Update the metadata if needed
                if (
                    MSMetaKeys.USER_ID.value not in customer.metadata
                    or MSMetaKeys.MEMBER_NUMBER.value not in customer.metadata
                ):
                    stripe.Customer.modify(
                        customer["id"],
                        metadata={
                            MSMetaKeys.USER_ID.value: member_info.member_id,
                            MSMetaKeys.MEMBER_NUMBER.value: member_info.member_number,
                        },
                    )
                return customer
            except InvalidRequestError as e:
                if "No such customer" in str(e.user_message):
                    print(
                        "Stripe customer not found, even though it existed in the database. Creating a new one."
                    )

        # If no customer is found, we create one
        customer = stripe.Customer.create(
            description="Created by Makeradmin",
            email=member_info.email,
            test_clock=test_clock,
            name=f"{member_info.firstname} {member_info.lastname}",
            metadata={
                MSMetaKeys.USER_ID.value: member_info.member_id,
                MSMetaKeys.MEMBER_NUMBER.value: member_info.member_number,
            },
        )

        # Note: Stripe doesn't update its search index of customers immediately,
        # so the new customer may not be visible to stripe.Customer.search for a few seconds.
        # Therefore we always try to find the customer by its ID, that we store in the database
        member_info.stripe_customer_id = customer.stripe_id
        db_session.commit()
        return customer
    except Exception as e:
        print(f"Unable to get or create stripe user: {e}")

    return None


# Binding period in months.
# Set to zero to disable binding periods.
# Setting it to 1 is not particularly useful, since it will be the same as a normal subscription.
BINDING_PERIOD = {
    SubscriptionType.MEMBERSHIP: 0,
    SubscriptionType.LAB: 2,
}

# Helper that can look up relevant price for the given member/subscription combo
# This would be a good place to implement discounts as the member_info could give
# the user a different price compared to the standard price for the products.
@dataclass
class ProductPricing:
    recurring_price: str
    binding_period_price: Optional[str]


# TODO: Would be a nice to cache this for an hour or so to avoid excessive lookups
def lookup_subscription_price_for(
    member_info: Optional[Member], subscription_type: SubscriptionType
) -> ProductPricing:
    products = stripe.Product.search(
        query=f"metadata['{MSMetaKeys.SUBSCRIPTION_TYPE.value}']:'{subscription_type.value}'"
    )
    assert (
        len(products.data) == 1
    ), f"Expected to find a single stripe product with metadata->{MSMetaKeys.SUBSCRIPTION_TYPE.value}={subscription_type.value}, but found {len(products.data)}"
    product = products.data[0]
    default_price = product["default_price"]
    assert type(default_price) == str

    prices = stripe.Price.list(product=product.stripe_id)
    if BINDING_PERIOD[subscription_type] > 0:
        binding_period = BINDING_PERIOD[subscription_type]
        # Filter by metadata
        starting_prices = [
            p
            for p in prices
            if MSMetaKeys.PRICE_TYPE.value in p["metadata"]
            if p["metadata"][MSMetaKeys.PRICE_TYPE.value]
            == PriceType.BINDING_PERIOD.value
        ]
        # Filter by period
        starting_prices = [
            p
            for p in starting_prices
            if p["recurring"]["interval"] == "month"
            and p["recurring"]["interval_count"] == binding_period
        ]
        assert (
            len(starting_prices) == 1
        ), f"Expected to find a single price for {subscription_type.name} with metadata->{MSMetaKeys.PRICE_TYPE.value}={PriceType.BINDING_PERIOD.value}, and a period of exactly {binding_period} months but found {len(starting_prices)}"
        binding_period_price = starting_prices[0]
    else:
        binding_period_price = None

    return ProductPricing(
        recurring_price=default_price, binding_period_price=binding_period_price
    )


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
    assert (
        earliest_start_at.tzinfo is not None
    ), "earliest_start_at must be timezone aware"

    memberships = get_membership_summary(member_id, earliest_start_at)
    was_already_member = False
    if (
        memberships.membership_active
        and subscription_type == SubscriptionType.MEMBERSHIP
    ):
        assert memberships.membership_end is not None
        subscription_start = calc_start_ts(
            memberships.membership_end, earliest_start_at
        )
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
) -> str:
    try:
        print(f"Attempting to start new subscription {subscription_type}")

        (was_already_member, subscription_start) = calc_subscription_start_time(
            member_id, subscription_type, earliest_start_at
        )

        member: Member = db_session.query(Member).get(member_id)
        stripe_customer = get_stripe_customer(member, test_clock)
        if stripe_customer is None:
            raise BadRequest(f"Unable to find corresponding stripe member {member}")
        assert member.stripe_customer_id == stripe_customer.stripe_id

        price = lookup_subscription_price_for(member, subscription_type)

        if subscription_type == SubscriptionType.MEMBERSHIP:
            current_subscription_id = member.stripe_membership_subscription_id
        elif subscription_type == SubscriptionType.LAB:
            current_subscription_id = member.stripe_labaccess_subscription_id
        else:
            assert False

        if current_subscription_id is not None:
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
                member = db_session.query(Member).get(member_id)

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
                            "price": price.binding_period_price,
                            "metadata": metadata,
                        },
                    ],
                    "collection_method": "charge_automatically",
                    "metadata": metadata,
                    "proration_behavior": "none",
                    "iterations": 1,
                }
            )

        phases.append(
            {
                "items": [
                    {
                        "price": price.recurring_price,
                        "metadata": metadata,
                    },
                ],
                "collection_method": "charge_automatically",
                "metadata": metadata,
                "proration_behavior": "none",
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

        db_session.commit()
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
    # If the subscription is not paused, we just do nothing.
    if subscription["pause_collection"] is None:
        return False

    # Resuming stripe subscriptions is possible,
    # but it was very tricky to do it while handling binding periods correctly.
    # So we just cancel the subscription and start a new one.
    # Much less code, much lower risk of bugs. Everyone is happy :)
    cancel_subscription(member_id, subscription_type, test_clock)
    start_subscription(member_id, subscription_type, test_clock, earliest_start_at)
    return True

    # (was_already_member, subscription_start) = calc_subscription_start_time(
    #     member_id, subscription_type, earliest_start_at
    # )

    # try:
    #     # The subscription might be a scheduled one so we need to check the id prefix
    #     # to determine which API to use.
    #     if subscription_id.startswith("sub_sched_"):
    #         # A subscription schedule cannot be paused.
    #         # Fortunately, we should never have to do this.
    #         # Subscriptions are paused when a new member signs up,
    #         # but hasn't yet signed the membership agreement.
    #         # But subscription schedules are only used for members
    #         # that already had membership when they signed up for the subscription.
    #         return False
    #     elif subscription_id.startswith("sub_"):
    #         subscription = stripe.Subscription.retrieve(subscription_id)
    #         # If the subscription is not paused, we just do nothing.
    #         if subscription["pause_collection"] is None:
    #             return False

    #         logger.info(f"Resuming subscription. It will start at {subscription_start}")
    #         if was_already_member:
    #             # If the member already had labaccess/membership at this time,
    #             # then we leave the billing anchor unchanged.
    #             # The member will then be billed at the normal time.
    #             # This is fine because when a subscription is started, it is scheduled
    #             # such that the billing cycle anchor lines up with when the member needs
    #             # to renew their subscription.
    #             stripe.Subscription.modify(
    #                 sid=subscription_id,
    #                 pause_collection={
    #                     "behavior": "void",
    #                     "resumes_at": int(subscription_start.timestamp()),
    #                 },
    #                 proration_behavior="none",
    #                 # billing_cycle_anchor="unchanged",
    #             )
    #         else:
    #             # This will resume the paused subscription and bill the member immediately.
    #             # The billing cycle anchor will be set to the current time, and since the member
    #             # does not have labaccess/membership at this time, we should not add any prorations.
    #             stripe.Subscription.modify(
    #                 sid=subscription_id,
    #                 pause_collection='', # None gets stripped out by the API, so we must use an empty string
    #                 billing_cycle_anchor="now",
    #                 proration_behavior="none",
    #             )
    #         return True
    #     else:
    #         assert False
    # except stripe.error.InvalidRequestError as e:
    #     if e.code == "resource_missing":
    #         # The subscription was already deleted
    #         # We might have missed the webhook to delete the reference from the member.
    #         # Or the webhook might be on its way.
    #         return False
    #     else:
    #         raise


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
            stripe.SubscriptionSchedule.release(subscription_id)
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
            db_session.commit()
        else:
            raise

    return True


def create_stripe_checkout_session(
    member_id: int,
    data: Any = None,
    test_clock: Optional[stripe.test_helpers.TestClock] = None,
) -> str:
    print("Creating stripe checkout session")
    checkout_session = None

    member: Member = db_session.query(Member).get(member_id)
    stripe_customer = get_stripe_customer(member, test_clock)
    if stripe_customer is None:
        raise BadRequest("Unable to find corresponding stripe member")

    metadata = {
        MSMetaKeys.USER_ID.value: member_id,
        MSMetaKeys.MEMBER_NUMBER.value: member.member_number,
    }

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="setup",
        metadata=metadata,
        test_clock=test_clock,
        customer=stripe_customer["id"],
        success_url=data["success_url"],
        cancel_url=data["cancel_url"],
    )

    # TODO: Handle normal shop payments?
    return checkout_session.url


def open_stripe_customer_portal(
    member_id: int, test_clock: Optional[stripe.test_helpers.TestClock]
) -> str:
    """Create a customer portal session and return the URL to which the user should be redirected."""
    member: Member = db_session.query(Member).get(member_id)
    stripe_customer = get_stripe_customer(member, test_clock)
    assert stripe_customer is not None

    billing_portal_session = stripe.billing_portal.Session.create(
        customer=stripe_customer["id"]
    )
    print(billing_portal_session)

    return billing_portal_session.url
