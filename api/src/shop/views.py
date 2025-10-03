from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from logging import getLogger
from typing import Any

from basic_types.enums import PriceLevel
from dataclasses_json import DataClassJsonMixin
from flask import Response, g, jsonify, make_response, request, send_file
from membership.models import Member
from multiaccessy.invite import (AccessyInvitePreconditionFailed,
                                 ensure_accessy_labaccess)
from service.api_definition import (DELETE, GET, MEMBER_EDIT, POST, PUBLIC,
                                    USER, WEBSHOP, WEBSHOP_EDIT)
from service.db import db_session
from service.entity import OrmSingeRelation, OrmSingleSingleRelation
from service.error import BadRequest, PreconditionFailed
from shop import service
from shop.entities import (category_entity, gift_card_content_entity,
                           gift_card_entity, product_accounting_entity,
                           product_action_entity, product_entity,
                           product_image_entity, transaction_account_entity,
                           transaction_action_entity,
                           transaction_content_entity,
                           transaction_cost_center_entity, transaction_entity)
from shop.models import Product, ProductImage, TransactionContent
from shop.pay import (CancelSubscriptionsRequest, SetupPaymentMethodResponse,
                      StartSubscriptionsRequest, cancel_subscriptions, pay,
                      register, setup_payment_method, start_subscriptions)
from shop.shop_data import (all_product_data, get_membership_products,
                            get_product_data, member_history, pending_actions,
                            receipt)
from shop.statistics import category_sales, product_sales
from shop.stripe_discounts import get_discount_fraction_off
from shop.stripe_event import stripe_callback
from shop.stripe_payment_intent import PartialPayment
from shop.stripe_setup import setup_stripe_products
from shop.stripe_subscriptions import (list_subscriptions,
                                       open_stripe_customer_portal)
from shop.transactions import (TransactionContent, commit_transaction_to_db,
                               payment_success, ship_labaccess_orders)
from sqlalchemy.exc import NoResultFound

logger = getLogger("makeradmin")

service.entity_routes(
    path="/category",
    entity=category_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


service.entity_routes(
    path="/product",
    entity=product_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


service.related_entity_routes(
    path="/product/<int:related_entity_id>/images",
    entity=product_image_entity,
    relation=OrmSingeRelation("images", "product_id"),
    permission_list=PUBLIC,
)


service.entity_routes(
    path="/product_action",
    entity=product_action_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)

service.entity_routes(
    path="/transaction_action",
    entity=transaction_action_entity,
    permission_read=WEBSHOP,
    permission_delete=WEBSHOP_EDIT,
)

service.related_entity_routes(
    path="/product/<int:related_entity_id>/actions",
    entity=product_action_entity,
    relation=OrmSingeRelation("actions", "product_id"),
    permission_list=WEBSHOP,
)


service.entity_routes(
    path="/transaction_content",
    entity=transaction_content_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
)


service.entity_routes(
    path="/transaction",
    entity=transaction_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
)

service.related_entity_routes(
    path="/transaction/<int:related_entity_id>/contents",
    entity=transaction_content_entity,
    relation=OrmSingeRelation("contents", "transaction_id"),
    permission_list=WEBSHOP,
)


service.related_entity_routes(
    path="/transaction/<int:related_entity_id>/actions",
    entity=transaction_action_entity,
    relation=OrmSingleSingleRelation("actions", TransactionContent, "transaction_id"),
    permission_list=WEBSHOP,
)

service.entity_routes(
    path="/gift-card",
    entity=gift_card_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
)

service.related_entity_routes(
    path="/gift-card/<int:related_entity_id>/products",
    entity=gift_card_content_entity,
    relation=OrmSingeRelation("products", "gift_card_id"),
    permission_list=WEBSHOP,
)

service.related_entity_routes(
    path="/member/<int:related_entity_id>/transactions",
    entity=transaction_entity,
    relation=OrmSingeRelation("member", "member_id"),
    permission_list=WEBSHOP,
)


service.entity_routes(
    path="/product_image",
    entity=product_image_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)

service.entity_routes(
    path="/transaction_account",
    entity=transaction_account_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)

service.entity_routes(
    path="/transaction_cost_center",
    entity=transaction_cost_center_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)

service.entity_routes(
    path="/accounting",
    entity=product_accounting_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


@service.route("/member/current/pending_actions", method=GET, permission=USER)
def pending_actions_for_member():
    return pending_actions(g.user_id)


@service.route("/member/current/transactions", method=GET, permission=USER)
def transactions_for_member():
    return member_history(g.user_id)


@service.route("/member/current/receipt/<int:transaction_id>", method=GET, permission=USER)
def receipt_for_member(transaction_id):
    return receipt(g.user_id, transaction_id)


@service.route("/member/current/accessy_invite", method=POST, permission=USER)
def accessy_invite() -> None:
    try:
        ensure_accessy_labaccess(member_id=g.user_id)
    except AccessyInvitePreconditionFailed as e:
        raise PreconditionFailed(message=str(e))


@service.route("/member/current/subscriptions", method=POST, permission=USER)
def start_subscriptions_route() -> None:
    try:
        data = StartSubscriptionsRequest.from_dict(request.json)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")
    return start_subscriptions(data, g.user_id)


@service.route("/member/current/subscriptions", method=DELETE, permission=USER)
def cancel_subscriptions_route() -> Any:
    try:
        data = CancelSubscriptionsRequest.from_dict(request.json)
    except Exception as e:
        raise BadRequest(message=f"Invalid data: {e}")
    return cancel_subscriptions(data, g.user_id)


@service.route("/member/current/subscriptions", method=GET, permission=USER)
def list_subscriptions_route() -> Any:
    return list_subscriptions(g.user_id)


@service.route("/member/current/stripe_customer_portal", method=GET, permission=PUBLIC)
def open_stripe_customer_portal_route() -> str:
    return open_stripe_customer_portal(g.user_id)


@service.route("/member/<int:member_id>/ship_labaccess_orders", method=POST, permission=MEMBER_EDIT)
def ship_labaccess_orders_endpoint(member_id: int) -> None:
    try:
        ship_labaccess_orders(member_id, skip_ensure_accessy=True)
        ensure_accessy_labaccess(member_id)  # Always do this, not only when the order is shipped.
    except AccessyInvitePreconditionFailed as e:
        raise PreconditionFailed(message=str(e))


@service.route("/product_data", method=GET, permission=PUBLIC)
def shop_data():
    response = jsonify({"status": "ok", "data": all_product_data()})

    # Allow caching of this response for a short amount of time
    response.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
    response.headers["Vary"] = "Accept-Encoding"
    return response


@service.route("/product_data/<int:product_id>", method=GET, permission=PUBLIC)
def product_data(product_id):
    response = jsonify({"status": "ok", "data": get_product_data(product_id)})

    # Allow caching of this response for a short amount of time
    response.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24}"
    response.headers["Vary"] = "Accept-Encoding"
    return response


@service.raw_route("/image/<int:image_id>")
def public_image(image_id: int) -> Response:
    try:
        image = (
            db_session.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.deleted_at.is_(None)).one()
        )
    except NoResultFound:
        return send_file("/work/default-product-image.png", mimetype="image/png")

    response = make_response(image.data)
    response.headers.set("Content-Type", image.type)
    response.headers.set("Max-Age", "36000")
    # Cache images for some time. We never update images, so setting immutable is fine.
    response.headers["Cache-Control"] = f"public, max-age={60 * 60 * 24 * 7}, immutable"
    response.headers["Vary"] = "Accept-Encoding"
    return response


@service.route("/register_page_data", method=GET, permission=PUBLIC)
def register_page_data():
    # Make sure subscription products have been created and are up to date
    setup_stripe_products()

    return {
        "membershipProducts": get_membership_products(),
        "productData": all_product_data(),
        "discounts": {
            price_level.value: get_discount_fraction_off(price_level).fraction_off for price_level in PriceLevel
        },
    }


@service.route("/pay", method=POST, permission=USER, commit_on_error=True)
def pay_route() -> PartialPayment:
    return pay(request.json, g.user_id)


# Used to just initiate a capture of a payment method via a setup intent
@service.route("/setup_payment_method", method=POST, permission=USER, commit_on_error=True)
def setup_payment_method_route() -> SetupPaymentMethodResponse:
    return setup_payment_method(request.json, g.user_id)


@service.route("/register", method=POST, permission=PUBLIC, commit_on_error=True)
def register_route() -> Any:
    assert request.remote_addr is not None
    return register(request.json, request.remote_addr, request.user_agent.string).to_dict()


@service.route("/stripe_callback", method=POST, permission=PUBLIC, commit_on_error=True)
def stripe_callback_route() -> None:
    stripe_callback(request.data, request.headers)


@service.route("/product/<int:product_id>/sales", method=GET, permission=WEBSHOP)
def product_sales_route(product_id: int) -> Any:
    start_str = request.args.get("start", default=None)
    start = datetime.fromisoformat(start_str) if start_str is not None else None

    end_str = request.args.get("end", default=None)
    end = datetime.fromisoformat(end_str) if end_str is not None else None
    return product_sales(product_id, start, end).to_dict()


@service.route("/category/<int:category_id>/sales", method=GET, permission=WEBSHOP)
def category_sales_route(category_id: int) -> Any:
    start_str = request.args.get("start", default=None)
    start = datetime.fromisoformat(start_str) if start_str is not None else None

    end_str = request.args.get("end", default=None)
    end = datetime.fromisoformat(end_str) if end_str is not None else None
    return category_sales(category_id, start, end).to_dict()


@dataclass
class GiftProductRequest(DataClassJsonMixin):
    product_id: int
    count: int
    member_ids: list[int]

@service.route("/gift-product", method=POST, permission=WEBSHOP_EDIT)
def gift_product() -> Any:
    """
    Create a gift transaction where someone donates money to purchase products for other members.
    The recipients get the product with zero payment required.
    """

    data = request.get_json()
    
    if not data:
        raise BadRequest("No JSON data provided")

    data = GiftProductRequest.from_json(data)

    if data.count <= 0:
        raise BadRequest("count must be a positive number")

    if len(data.member_ids) == 0:
        raise BadRequest("At least one member_id is required")
    
    # Get the product
    try:
        product = db_session.get(Product, data.product_id)
        if not product:
            raise BadRequest(f"Product with id {data.product_id} not found")
    except Exception:
        raise BadRequest(f"Product with id {data.product_id} not found")
    
    # Verify all members exist
    for member_id in data.member_ids:
        try:
            member = db_session.get(Member, member_id)
            if not member:
                raise BadRequest(f"Member with id {member_id} not found")
        except Exception:
            raise BadRequest(f"Member with id {member_id} not found")

    # Create gift transactions for each member - each gets the product for free
    created_transactions = []
    
    for member_id in data.member_ids:
        # Create transaction content for the product with zero amount (gift)
        transaction_content = TransactionContent(
            product_id=data.product_id,
            count=data.count,
            amount=Decimal('0.00')  # The recipient pays nothing
        )
        
        # Create the transaction with zero amount
        transaction = commit_transaction_to_db(
            member_id=member_id,
            total_amount=Decimal('0.00'),  # The recipient pays nothing
            contents=[transaction_content]
        )
        
        # Mark transaction as completed immediately since no payment is required
        payment_success(transaction)
        created_transactions.append(transaction.id)
    
    return {
        "transaction_ids": created_transactions
    }
