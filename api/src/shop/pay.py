from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from typing import Any, List, Literal, Optional, Tuple, Union
from dataclasses_json import DataClassJsonMixin, dataclass_json

import stripe
from stripe.error import CardError
from shop.stripe_constants import MakerspaceMetadataKeys
from shop.stripe_setup_intent import check_next_action
from membership.models import Member
from shop.models import Transaction
from shop.stripe_subscriptions import (
    SubscriptionType,
    attach_and_set_default_payment_method,
    get_stripe_customer,
    start_subscription,
)
from service.db import db_session
from core import auth
from membership.views import member_entity
from service.error import BadRequest
from shop.api_schemas import validate_data, purchase_schema, register_schema
from shop.shop_data import get_membership_products, special_product_data
from shop.stripe_payment_intent import PartialPayment, PaymentAction, pay_with_stripe
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
        stripe_reference_id=payment_method_id,
    )

    action_info = pay_with_stripe(transaction, payment_method_id)

    return transaction, action_info


def pay(data: Any, member_id: int) -> PartialPayment:
    purchase = Purchase.from_dict(data)

    # Prevent service accounts from purchasing.
    if member_id <= 0:
        raise BadRequest("You must be a member to purchase materials and tools.")

    # This will raise if the payment fails.
    transaction, action_info = make_purchase(member_id=member_id, purchase=purchase)

    return PartialPayment(
        transaction_id=transaction.id,
        action_info=action_info,
    )


def register(data: Any, remote_addr: str, user_agent: str):

    validate_data(register_schema, data or {})

    products = get_membership_products()

    purchase = data["purchase"]

    cart = purchase["cart"]
    if len(cart) != 1:
        raise BadRequest(message="The purchase must contain exactly one item.")

    item = cart[0]
    if item["count"] != 1:
        raise BadRequest(message="The purchase must contain exactly one item.")

    product_id = item["id"]
    if product_id not in (p.id for p in products):
        raise BadRequest(
            message=f"Not allowed to purchase the product with id {product_id} when registring."
        )

    # This will raise if the creation fails, if it succeeds it will commit the member.
    member_id = member_entity.create(data.get("member", {}))["member_id"]

    # This will raise if the payment fails.
    transaction, action_info = make_purchase(
        member_id=member_id, purchase=purchase, activates_member=True
    )

    # If the pay succeeded (not same as the payment is completed) and the member does not already exists,
    # the user will be logged in.
    token = auth.force_login(remote_addr, user_agent, member_id)["access_token"]

    return {
        "transaction_id": transaction.id,
        "token": token,
        "action_info": action_info,
    }


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
        if not self.email.strip() or "@" not in self.email:
            raise BadRequest(message="Email is required.")
        if not self.phone.strip():
            raise BadRequest(message="Phone is required.")
        if not self.zipCode.strip():
            raise BadRequest(message="Zip code is required.")


@dataclass
class RegisterRequest(DataClassJsonMixin):
    purchase: Purchase
    setup_intent_id: Optional[str]
    member: MemberInfo
    subscriptions: List[SubscriptionType]


class RegisterResponseType(str, Enum):
    Success = "success"
    RequiresAction = "requires_action"
    Wait = "wait"
    Failed = "failed"


@dataclass
class RegisterResponse(DataClassJsonMixin):
    setup_intent_id: str
    type: RegisterResponseType
    token: Optional[str]
    action_info: Optional[PaymentAction]
    error: Optional[str] = None


class SetupIntentStatus(Enum):
    RequiresPaymentMethod = "requires_payment_method"
    RequiresConfirmation = "requires_confirmation"
    RequiresAction = "requires_action"
    Processing = "processing"
    Canceled = "canceled"
    Succeeded = "succeeded"


@dataclass
class RegistrationFailed(Exception):
    response: RegisterResponse


def register2(data_dict: Any, remote_addr: str, user_agent: str) -> RegisterResponse:
    try:
        data = RegisterRequest.from_dict(data_dict)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")

    data.member.validate()
    if len(set(data.subscriptions)) != len(data.subscriptions):
        raise BadRequest(message="Duplicate subscriptions.")

    try:
        payment_method = stripe.PaymentMethod.retrieve(
            data.purchase.stripe_payment_method_id
        )
    except:
        raise BadRequest(message="The payment method is not valid.")

    if data.setup_intent_id is None:
        # stripe_customer = get_stripe_customer(member, test_clock=None)
        # assert stripe_customer is not None

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
                },
                commit=False,
            )["member_id"]
            member = db_session.query(Member).get(member_id)
            assert member is not None
            member.stripe_customer_id = stripe_customer.stripe_id

            while True:
                status = SetupIntentStatus(setup_intent["status"])
                if status == SetupIntentStatus.RequiresPaymentMethod:
                    # This can happen if the card was declined.
                    # In that case the user will just have to try again.
                    # We delete the customer just to keep things tidy. It's not strictly necessary.
                    stripe.Customer.delete(stripe_customer.stripe_id)
                    raise RegistrationFailed(
                        RegisterResponse(
                            type=RegisterResponseType.Failed,
                            setup_intent_id=setup_intent.stripe_id,
                            token=None,
                            error=setup_intent["last_setup_error"]["message"],
                            action_info=None,
                        )
                    )
                elif status == SetupIntentStatus.RequiresConfirmation:
                    try:
                        setup_intent = stripe.SetupIntent.confirm(
                            setup_intent.stripe_id
                        )
                    except CardError as e:
                        # This can happen if the card was declined in *some* cases.
                        # In particular, it happens if you try to use a real card in a testing environment.
                        raise RegistrationFailed(
                            RegisterResponse(
                                type=RegisterResponseType.Failed,
                                setup_intent_id=setup_intent.stripe_id,
                                token=None,
                                error=e.error.message,
                                action_info=None,
                            )
                        )
                    # assert False, "Should not be required, as we provided the payment info at creation"
                    continue
                elif status == SetupIntentStatus.RequiresAction:
                    payment_action = check_next_action(setup_intent)
                    raise RegistrationFailed(
                        RegisterResponse(
                            type=RegisterResponseType.RequiresAction,
                            setup_intent_id=setup_intent.stripe_id,
                            token=None,
                            action_info=payment_action,
                        )
                    )
                elif status == SetupIntentStatus.Processing:
                    raise RegistrationFailed(
                        RegisterResponse(
                            type=RegisterResponseType.Wait,
                            setup_intent_id=setup_intent.stripe_id,
                            token=None,
                            action_info=None,
                        )
                    )

                elif status == SetupIntentStatus.Succeeded:
                    # Yay. The setup intent is verified.
                    # This means we should be able to charge the card with WHATEVER WE WANT!
                    # HAHA! Let's drain the card!
                    # No, just kidding. We will just charge the card with the amount for the purchase.

                    products = special_product_data()

                    purchase = data.purchase

                    cart = purchase.cart
                    if len(cart) > 1:
                        raise BadRequest(
                            message="The purchase must contain at most one item."
                        )

                    if len(cart) > 0:
                        item = cart[0]
                        if item.count != 1:
                            raise BadRequest(
                                message="The purchase must contain exactly one item."
                            )

                        product_id = item.id
                        # Make sure it is a special product, but not a subscription product
                        if product_id not in (
                            p.id
                            for p in products
                            if MakerspaceMetadataKeys.SUBSCRIPTION_TYPE
                            not in p.product_metadata
                        ):
                            raise BadRequest(
                                message=f"Not allowed to purchase the product with id {product_id} when registring."
                            )

                        # This will raise if the payment fails.
                        transaction, action_info = make_purchase(
                            member_id=member_id,
                            purchase=purchase,
                            activates_member=False,
                        )
                        if action_info is not None:
                            # We have already done a setup intent, so the card should not require additional verification.
                            # If it does, we just fail.
                            # There are probably cards for which this can happen. But how could we possibly handle
                            # subscriptions in that case?
                            raise RegistrationFailed(
                                RegisterResponse(
                                    type=RegisterResponseType.Failed,
                                    setup_intent_id=setup_intent.stripe_id,
                                    error="Your card does not allow this payment without additional verification.",
                                    token=None,
                                    action_info=None,
                                )
                            )

                    for subscription in data.subscriptions:
                        # Note: This will *not* raise in case the user has not enough funds.
                        # In that case we should send an email to the user.
                        start_subscription(
                            member.member_id, subscription, test_clock=None
                        )

                    # If the pay succeeded (not same as the payment is completed) and the member does not already exists,
                    # the user will be logged in.
                    token = auth.force_login(remote_addr, user_agent, member_id)[
                        "access_token"
                    ]

                    # This will get the stripe customer, and in the process update its metadata fields.
                    get_stripe_customer(member, test_clock=None)
                    activate_member(member)

                    return RegisterResponse(
                        type=RegisterResponseType.Success,
                        setup_intent_id=setup_intent.stripe_id,
                        token=token,
                        action_info=None,
                    )
                elif status == SetupIntentStatus.Canceled:
                    stripe.Customer.delete(stripe_customer.stripe_id)
                    raise BadRequest(message="The payment was canceled.")
                else:
                    assert False, f"Unknown status {status}"
    except RegistrationFailed as e:
        return e.response
