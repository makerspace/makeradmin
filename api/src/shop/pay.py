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
