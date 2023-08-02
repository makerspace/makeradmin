from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import re
from logging import getLogger
from typing import Any, List, Literal, Optional, Tuple, Union
from dataclasses_json import DataClassJsonMixin, dataclass_json

import stripe
from stripe.error import CardError
from membership.enums import PriceLevel
from shop.stripe_constants import MakerspaceMetadataKeys
from shop.stripe_setup_intent import check_next_action
from membership.models import Member
from shop.models import Transaction
from shop.stripe_subscriptions import (
    SubscriptionType,
    cancel_subscription,
    get_stripe_customer,
    start_subscription,
)
from service.db import db_session
from core import auth
from membership.views import member_entity
from service.error import BadRequest, UnprocessableEntity
from shop.shop_data import special_product_data
from shop.stripe_payment_intent import PartialPayment, PaymentAction, pay_with_stripe
from shop.stripe_payment_intent import (
    PartialPayment,
    PaymentAction,
    PaymentIntentResult,
    confirm_stripe_payment_intent,
    pay_with_stripe,
)
from shop.transactions import Purchase, activate_member, create_transaction

logger = getLogger("makeradmin")


def make_purchase(
    member_id: int, purchase: Purchase, activates_member: bool = False
) -> Tuple[Transaction, Optional[PaymentAction]]:
    """Pay using the data in purchase, the purchase structure should be validated according to schema."""

    payment_method_id: str = purchase.stripe_payment_method_id

    transaction = create_transaction(
        member_id=member_id,
        purchase=purchase,
        activates_member=activates_member,
    )
    action_info = pay_with_stripe(transaction, payment_method_id)

    return transaction, action_info


def pay(data: Any, member_id: int) -> PartialPayment:
    purchase = Purchase.from_dict(data)

    # Prevent service accounts from purchasing.
    if member_id <= 0:
        raise BadRequest("You must be a member to purchase materials and tools.")

    if purchase.transaction_id is not None:
        # This is a retry of an in-progress payment.
        return confirm_stripe_payment_intent(purchase.transaction_id)
    else:
        # This will raise if the payment fails.
        transaction, action_info = make_purchase(member_id=member_id, purchase=purchase)

        return PartialPayment(
            type=PaymentIntentResult.Success if action_info is None else PaymentIntentResult.RequiresAction,
            transaction_id=transaction.id,
            action_info=action_info,
        )


@dataclass
class MemberInfo(DataClassJsonMixin):
    firstName: str
    lastName: str
    email: str
    phone: str
    zipCode: str

    def validate(self) -> None:
        if not self.firstName.strip():
            raise BadRequest(message="Firstname is required.")
        if not self.lastName.strip():
            raise BadRequest(message="Lastname is required.")
        if not self.email.strip():
            raise BadRequest(message="Email is required.")
        if not self.phone.strip():
            raise BadRequest(message="Phone is required.")
        if not self.zipCode.strip():
            raise BadRequest(message="Zip code is required.")

        if not re.match(
            "^[a-zA-Z0-9.!#$%&'*+\\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
            "[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
            self.email.strip(),
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
    setup_intent_id: Optional[str]
    stripe_payment_method_id: str


@dataclass
class RegisterRequest(DataClassJsonMixin):
    purchase: Purchase
    setup_intent_id: Optional[str]
    member: MemberInfo
    subscriptions: List[SubscriptionStart]
    discount: Optional[DiscountRequest]


class SetupIntentResult(str, Enum):
    Success = "success"
    RequiresAction = "requires_action"
    Wait = "wait"
    Failed = "failed"


@dataclass
class StartSubscriptionsResponse(DataClassJsonMixin):
    setup_intent_id: str
    type: SetupIntentResult
    action_info: Optional[PaymentAction]
    error: Optional[str] = None


@dataclass
class RegisterResponse(DataClassJsonMixin):
    setup_intent_id: str
    type: SetupIntentResult
    token: Optional[str]
    action_info: Optional[PaymentAction]
    member_id: Optional[int]
    error: Optional[str] = None


class SetupIntentStatus(Enum):
    RequiresPaymentMethod = "requires_payment_method"
    RequiresConfirmation = "requires_confirmation"
    RequiresAction = "requires_action"
    Processing = "processing"
    Canceled = "canceled"
    Succeeded = "succeeded"


@dataclass
class SetupIntentFailed(Exception):
    type: SetupIntentResult
    action_info: Optional[PaymentAction]
    error: Optional[str] = None


def validate_cart(purchase: Purchase) -> None:
    products = special_product_data()

    cart = purchase.cart
    if len(cart) > 1:
        raise BadRequest(message="The purchase must contain at most one item.")

    if len(cart) > 0:
        item = cart[0]
        if item.count != 1:
            raise BadRequest(message="The purchase must contain exactly one item.")

        product_id = item.id
        # Make sure it is a special product, but not a subscription product
        if product_id not in (
            p.id for p in products if MakerspaceMetadataKeys.SUBSCRIPTION_TYPE not in p.product_metadata
        ):
            raise BadRequest(message=f"Not allowed to purchase the product with id {product_id} when registring.")


def handle_setup_intent(setup_intent: stripe.SetupIntent) -> None:
    while True:
        status = SetupIntentStatus(setup_intent["status"])
        if status == SetupIntentStatus.RequiresPaymentMethod:
            # This can happen if the card was declined.
            # In that case the user will just have to try again.
            raise SetupIntentFailed(
                type=SetupIntentResult.Failed,
                error=setup_intent["last_setup_error"]["message"],
                action_info=None,
            )
        elif status == SetupIntentStatus.RequiresConfirmation:
            try:
                setup_intent = stripe.SetupIntent.confirm(setup_intent.stripe_id)
            except CardError as e:
                # This can happen if the card was declined in *some* cases.
                # In particular, it happens if you try to use a real card in a testing environment.
                raise SetupIntentFailed(
                    type=SetupIntentResult.Failed,
                    error=e.error.message,
                    action_info=None,
                )
            continue
        elif status == SetupIntentStatus.RequiresAction:
            payment_action = check_next_action(setup_intent)
            raise SetupIntentFailed(
                type=SetupIntentResult.RequiresAction,
                action_info=payment_action,
                error=None,
            )
        elif status == SetupIntentStatus.Processing:
            raise SetupIntentFailed(type=SetupIntentResult.Wait, action_info=None, error=None)
        elif status == SetupIntentStatus.Succeeded:
            # Yay!

            # Mark this payment method as the customer's default payment method for the future.
            # The customer must have a default payment method so that invoices for a subscription can be charged.
            stripe.Customer.modify(
                setup_intent["customer"],
                invoice_settings={"default_payment_method": setup_intent["payment_method"]},
            )

            # TODO: Should we delete all previous payment methods to keep things clean?
            return
        elif status == SetupIntentStatus.Canceled:
            raise BadRequest(message="The payment was canceled.")
        else:
            assert False, f"Unknown status {status}"


def cancel_subscriptions(data_dict: Any, user_id: int) -> None:
    try:
        data = CancelSubscriptionsRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    member = db_session.query(Member).get(user_id)
    assert member is not None

    if SubscriptionType.MEMBERSHIP in data.subscriptions and SubscriptionType.LAB not in data.subscriptions:
        # This should be handled automatically by the frontend with a nice popup, but we will enforce it here
        data.subscriptions.append(SubscriptionType.LAB)

    for sub in data.subscriptions:
        cancel_subscription(member.member_id, sub, test_clock=None)


def start_subscriptions(data_dict: Any, user_id: int) -> StartSubscriptionsResponse:
    try:
        data = StartSubscriptionsRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    member = db_session.query(Member).get(user_id)
    assert member is not None

    stripe_customer = get_stripe_customer(member, test_clock=None)
    assert stripe_customer is not None

    try:
        payment_method = stripe.PaymentMethod.retrieve(data.stripe_payment_method_id)
    except:
        raise BadRequest(message="The payment method is not valid.")

    if data.setup_intent_id is None:
        # TODO: If a customer already has a payment method attached, we should use that instead of creating a new one.
        # In that case, we shouldn't show the card input to the user.
        setup_intent = stripe.SetupIntent.create(
            payment_method_types=["card"],
            metadata={},
            payment_method=payment_method.stripe_id,
            customer=stripe_customer.stripe_id,
        )
    else:
        setup_intent = stripe.SetupIntent.retrieve(data.setup_intent_id)
        if stripe_customer.stripe_id != setup_intent["customer"]:
            raise BadRequest(message="The payment intent is not for the currently logged in member.")

    try:
        handle_setup_intent(setup_intent)
    except SetupIntentFailed as e:
        return StartSubscriptionsResponse(
            type=e.type,
            setup_intent_id=setup_intent.stripe_id,
            action_info=e.action_info,
            error=e.error,
        )

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

    return StartSubscriptionsResponse(
        type=SetupIntentResult.Success,
        setup_intent_id=setup_intent.stripe_id,
        action_info=None,
        error=None,
    )


def register(data_dict: Any, remote_addr: str, user_agent: str) -> RegisterResponse:
    try:
        data = RegisterRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    data.member.validate()
    validate_cart(data.purchase)

    if len(set([s.subscription for s in data.subscriptions])) != len(data.subscriptions):
        raise BadRequest(message="Duplicate subscriptions.")

    try:
        payment_method = stripe.PaymentMethod.retrieve(data.purchase.stripe_payment_method_id)
    except:
        raise BadRequest(message="The payment method is not valid.")

    if data.setup_intent_id is None:
        # Create a new stripe customer.
        # If the verification fails, we just forget about the customer
        stripe_customer = stripe.Customer.create(
            description="Created by Makeradmin",
            email=data.member.email,
            test_clock=None,
            name=f"{data.member.firstName} {data.member.lastName}",
            metadata={
                MakerspaceMetadataKeys.PENDING_MEMBER.value: "pending",
            },
        )

        setup_intent = stripe.SetupIntent.create(
            payment_method_types=["card"],
            metadata={},
            payment_method=payment_method.stripe_id,
            customer=stripe_customer.stripe_id,
        )
    else:
        setup_intent = stripe.SetupIntent.retrieve(data.setup_intent_id)
        stripe_customer = stripe.Customer.retrieve(setup_intent["customer"])

    try:
        with db_session.begin_nested():
            # This will raise if the creation fails, if it succeeds it will add the member.
            # However, since we are in a transaction, the member will not be fully added until the transaction is committed.
            # What happens now is that we speculatively create the member, and if the payment fails, or requires more
            # verification steps, we just rollback the transaction.
            # This ensures that the member can be created before the payment is completed.
            member_id: int = member_entity.create(
                {
                    "firstname": data.member.firstName,
                    "lastname": data.member.lastName,
                    "email": data.member.email,
                    "phone": data.member.phone,
                    "address_zipcode": data.member.zipCode,
                    "price_level": (
                        data.discount.price_level if data.discount is not None else PriceLevel.Normal
                    ).value,
                    "price_level_motivation": data.discount.message if data.discount is not None else None,
                },
                commit=False,
            )["member_id"]
            member = db_session.query(Member).get(member_id)
            assert member is not None
            member.stripe_customer_id = stripe_customer.stripe_id

            try:
                handle_setup_intent(setup_intent)
            except SetupIntentFailed as e:
                if e.type == SetupIntentResult.Failed:
                    # We delete the customer just to keep things tidy. It's not strictly necessary.
                    stripe.Customer.delete(stripe_customer.stripe_id)
                raise
            except BadRequest:
                # We delete the customer just to keep things tidy. It's not strictly necessary.
                stripe.Customer.delete(stripe_customer.stripe_id)
                raise

            # Yay. The setup intent is verified.
            # This means we should be able to charge the card with WHATEVER WE WANT!
            # HAHA! Let's drain the card!
            # No, just kidding. We will just charge the card with the amount for the purchase.
            if len(data.purchase.cart) > 0:
                # This will raise if the payment fails.
                transaction, action_info = make_purchase(
                    member_id=member_id,
                    purchase=data.purchase,
                    activates_member=False,
                )
                if action_info is not None:
                    logger.error(
                        "Purchase could not be completed. Card requires additional verification: %s",
                        action_info.type,
                    )
                    # We have already done a setup intent, so the card should not require additional verification.
                    # If it does, we just fail.
                    # There are probably cards for which this can happen. But how could we possibly handle
                    # subscriptions in that case?
                    stripe.Customer.delete(stripe_customer.stripe_id)
                    raise SetupIntentFailed(
                        type=SetupIntentResult.Failed,
                        error="Your card does not allow this payment without additional verification.",
                        action_info=None,
                    )

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

            # If the pay succeeded (not same as the payment is completed) and the member does not already exists,
            # the user will be logged in.
            token = auth.force_login(remote_addr, user_agent, member_id)["access_token"]

            # This will get the stripe customer, and in the process update its metadata fields.
            get_stripe_customer(member, test_clock=None)
            activate_member(member)

            return RegisterResponse(
                type=SetupIntentResult.Success,
                setup_intent_id=setup_intent.stripe_id,
                token=token,
                action_info=None,
                member_id=member_id,
            )
    except SetupIntentFailed as e:
        return RegisterResponse(
            type=e.type,
            setup_intent_id=setup_intent.stripe_id,
            token=None,
            action_info=e.action_info,
            error=e.error,
            member_id=None,
        )
