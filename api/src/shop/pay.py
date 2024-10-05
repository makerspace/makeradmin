import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from logging import getLogger
from typing import Any, List, Optional

import stripe
from basic_types.enums import PriceLevel
from core import auth
from dataclasses_json import DataClassJsonMixin
from membership.models import Member, Span
from membership.views import member_entity
from service.db import db_session
from service.error import BadRequest, UnprocessableEntity

from shop.models import Product, StripePending, Transaction, TransactionAction, TransactionContent
from shop.stripe_constants import MakerspaceMetadataKeys
from shop.stripe_customer import get_and_sync_stripe_customer
from shop.stripe_payment_intent import (
    PartialPayment,
    PaymentAction,
    confirm_stripe_payment_intent,
    pay_with_stripe,
)
from shop.stripe_setup_intent import SetupIntentFailed, SetupIntentResult, handle_setup_intent
from shop.stripe_subscriptions import (
    SubscriptionType,
    cancel_subscription,
    start_subscription,
)
from shop.stripe_util import retry
from shop.transactions import Purchase, create_transaction

logger = getLogger("makeradmin")


def make_purchase(member_id: int, purchase: Purchase) -> Transaction:
    """Pay using the data in purchase, the purchase structure should be validated according to schema."""

    payment_method_id: str = purchase.stripe_payment_method_id

    transaction = create_transaction(member_id=member_id, purchase=purchase)

    # If this purchase will start a subscription, then the payment method should be attached to the customer so that it can be used for the subscription.
    starts_subscription = False
    for item in purchase.cart:
        product = db_session.query(Product).get(item.id)
        assert product is not None
        starts_subscription |= product.get_metadata(MakerspaceMetadataKeys.SUBSCRIPTION_TYPE, None) is not None

    pay_with_stripe(transaction, payment_method_id, setup_future_usage=starts_subscription)

    return transaction


def pay(data: Any, member_id: int) -> PartialPayment:
    try:
        purchase = Purchase.from_dict(data)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    # Prevent service accounts from purchasing.
    if member_id <= 0:
        raise BadRequest("You must be a member to purchase materials and tools.")

    if purchase.transaction_id is not None:
        # This is a retry of an in-progress payment.
        return confirm_stripe_payment_intent(purchase.transaction_id)
    else:
        # This will raise if the payment fails.
        transaction = make_purchase(member_id=member_id, purchase=purchase)
        return confirm_stripe_payment_intent(transaction.id)


@dataclass
class MemberInfo(DataClassJsonMixin):
    firstName: str
    lastName: str
    email: str
    phone: str
    zipCode: int

    def strip(self) -> None:
        self.firstName = self.firstName.strip()
        self.lastName = self.lastName.strip()
        self.email = self.email.strip()
        self.phone = self.phone.strip()

    def validate(self) -> None:
        if not self.firstName:
            raise BadRequest(message="Firstname is required.")
        if not self.lastName:
            raise BadRequest(message="Lastname is required.")
        if not self.email:
            raise BadRequest(message="Email is required.")
        if not self.phone:
            raise BadRequest(message="Phone is required.")
        if self.zipCode <= 0:
            raise BadRequest(message="Zip code must be positive")

        if not re.match(
            "^[a-zA-Z0-9.!#$%&'*+\\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
            "[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
            self.email,
        ):
            raise UnprocessableEntity(message="Email is not valid.")


@dataclass
class SubscriptionStart(DataClassJsonMixin):
    subscription: SubscriptionType
    expected_to_pay_now: Decimal
    expected_to_pay_recurring: Decimal


@dataclass
class DiscountRequest(DataClassJsonMixin):
    price_level: PriceLevel
    message: str


@dataclass
class CancelSubscriptionsRequest(DataClassJsonMixin):
    subscriptions: List[SubscriptionType]


@dataclass
class StartSubscriptionsRequest(DataClassJsonMixin):
    subscriptions: List[SubscriptionStart]


@dataclass
class RegisterRequest(DataClassJsonMixin):
    member: MemberInfo
    discount: Optional[DiscountRequest]


@dataclass
class RegisterResponse(DataClassJsonMixin):
    token: str
    member_id: int


@dataclass
class SetupPaymentMethodRequest(DataClassJsonMixin):
    stripe_payment_method_id: str
    setup_intent_id: Optional[str]


@dataclass
class SetupPaymentMethodResponse(DataClassJsonMixin):
    setup_intent_id: str
    type: SetupIntentResult
    action_info: Optional[PaymentAction]
    error: Optional[str] = None


def setup_payment_method(data_dict: Any, member_id: int) -> SetupPaymentMethodResponse:
    try:
        data = SetupPaymentMethodRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    member = db_session.query(Member).get(member_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {member_id}")

    stripe_customer = get_and_sync_stripe_customer(member)
    if stripe_customer is None:
        raise BadRequest(f"Unable to find corresponding stripe member {member}")

    setup_intent_id = data.setup_intent_id
    if setup_intent_id is None:
        try:
            payment_method = retry(lambda: stripe.PaymentMethod.retrieve(data.stripe_payment_method_id))
        except:
            raise BadRequest(message="The payment method is not valid.")

        setup_intent = retry(
            lambda: stripe.SetupIntent.create(
                payment_method_types=["card"],
                metadata={},
                payment_method=payment_method.id,
                customer=stripe_customer.id,
            )
        )
    else:
        setup_intent = retry(lambda: stripe.SetupIntent.retrieve(setup_intent_id))

    try:
        handle_setup_intent(setup_intent)
    except SetupIntentFailed as e:
        return SetupPaymentMethodResponse(
            type=e.type,
            setup_intent_id=setup_intent.id,
            action_info=e.action_info,
            error=e.error,
        )

    return SetupPaymentMethodResponse(
        type=SetupIntentResult.Success,
        setup_intent_id=setup_intent.id,
        action_info=None,
        error=None,
    )


def cancel_subscriptions(data_dict: Any, user_id: int) -> None:
    try:
        data = CancelSubscriptionsRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    member = db_session.query(Member).get(user_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {user_id}")

    if SubscriptionType.MEMBERSHIP in data.subscriptions and SubscriptionType.LAB not in data.subscriptions:
        # This should be handled automatically by the frontend with a nice popup, but we will enforce it here
        data.subscriptions.append(SubscriptionType.LAB)

    for sub in data.subscriptions:
        cancel_subscription(member.member_id, sub, test_clock=None)


def start_subscriptions(data_dict: Any, user_id: int) -> None:
    try:
        data = StartSubscriptionsRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    member = db_session.query(Member).get(user_id)
    if member is None:
        raise BadRequest(f"Unable to find member with id {user_id}")

    stripe_customer = get_and_sync_stripe_customer(member)
    assert stripe_customer is not None

    if not stripe_customer.invoice_settings["default_payment_method"]:
        raise BadRequest(message="You must add a default payment method before starting a subscription.")

    for subscription in data.subscriptions:
        # Note: This will *not* raise in case the user has not enough funds.
        # In that case we should send an email to the user.
        start_subscription(
            member.member_id,
            subscription.subscription,
            test_clock=None,
            expected_to_pay_now=subscription.expected_to_pay_now,
            expected_to_pay_recurring=subscription.expected_to_pay_recurring,
        )


def cleanup_pending_members(relevant_email: str) -> None:
    """
    Delete all pending members that have not been activated within the last hour.
    This is to prevent the database from filling up with pending members.
    We also delete all pending members with the same email as the new member, in case their payment failed and they want to retry.
    """
    members_to_delete = (
        db_session.query(Member)
        .filter(
            (Member.pending_activation == True)
            & (
                (Member.email == relevant_email) | (Member.created_at < datetime.now(timezone.utc) - timedelta(hours=1))
            ),
        )
        .all()
    )

    for member in members_to_delete:
        # We delete the customer just to keep things tidy. It's not strictly necessary.
        stripe_customer_id = member.stripe_customer_id
        if stripe_customer_id is not None:
            try:
                retry(lambda: stripe.Customer.delete(stripe_customer_id))
            except:
                # If it cannot be deleted, we don't care
                pass

    # Delete the pending members and any spans and transactions that belonged to them
    db_session.query(Span).filter(Span.member_id.in_([m.member_id for m in members_to_delete])).delete()
    transactions_to_delete = db_session.query(Transaction).filter(
        Transaction.member_id.in_([m.member_id for m in members_to_delete])
    )
    content_to_delete = db_session.query(TransactionContent).filter(
        TransactionContent.transaction_id.in_([t.id for t in transactions_to_delete])
    )
    db_session.query(StripePending).filter(
        StripePending.transaction_id.in_([t.id for t in transactions_to_delete])
    ).delete()
    db_session.query(TransactionAction).filter(
        TransactionAction.content_id.in_([t.id for t in content_to_delete])
    ).delete()
    db_session.query(TransactionContent).filter(
        TransactionContent.transaction_id.in_([t.id for t in transactions_to_delete])
    ).delete()
    db_session.query(Transaction).filter(Transaction.member_id.in_([m.member_id for m in members_to_delete])).delete()
    db_session.query(Member).filter(Member.member_id.in_([m.member_id for m in members_to_delete])).delete()


def register(data_dict: Any, remote_addr: str, user_agent: str) -> RegisterResponse:
    try:
        data = RegisterRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    data.member.strip()
    data.member.validate()

    cleanup_pending_members(data.member.email)

    # This will raise if the creation fails, if it succeeds it will add the member.
    member_id: int = member_entity.create(
        {
            "firstname": data.member.firstName,
            "lastname": data.member.lastName,
            "email": data.member.email,
            "phone": data.member.phone,
            "address_zipcode": data.member.zipCode,
            # Mark the member instantly as pending
            # The member will be activated on the first successful purchase
            "pending_activation": True,
            "price_level": (data.discount.price_level if data.discount is not None else PriceLevel.Normal).value,
            "price_level_motivation": data.discount.message if data.discount is not None else None,
        },
        commit=True,
    )["member_id"]

    # Mark the member as deleted, so that it is not visible in the member list, and it cannot be used to log in
    # We cannot pass the deleted_at parameter to the create function because it the API prevents that field from being set.
    member = db_session.query(Member).filter(Member.member_id == member_id).one()
    member.deleted_at = datetime.now(timezone.utc)
    db_session.flush()

    token = auth.force_login(remote_addr, user_agent, member_id)["access_token"]
    return RegisterResponse(
        token=token,
        member_id=member_id,
    )
