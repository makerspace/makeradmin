from dataclasses import dataclass
from typing import Any
from flask import Response, g, request, send_file, make_response, redirect, jsonify
from sqlalchemy.exc import NoResultFound
from membership.enums import PriceLevel
from shop.stripe_discounts import get_discount_fraction_off

from multiaccessy.invite import AccessyInvitePreconditionFailed, ensure_accessy_labaccess
from service.api_definition import WEBSHOP, WEBSHOP_EDIT, PUBLIC, GET, USER, POST, DELETE, Arg, WEBSHOP_ADMIN, MEMBER_EDIT
from service.db import db_session
from service.entity import OrmSingeRelation, OrmSingleSingleRelation
from service.error import InternalServerError, PreconditionFailed
from shop import service
from shop.entities import product_image_entity, transaction_content_entity, transaction_entity, \
    transaction_action_entity, product_entity, category_entity, product_action_entity
from shop.models import TransactionContent, ProductImage
from shop.pay import RegisterResponse, pay, register, register2

from shop.stripe_subscriptions import start_subscription, cancel_subscription
from shop.stripe_subscriptions import open_stripe_customer_portal

from shop.stripe_payment_intent import PartialPayment, confirm_stripe_payment_intent
from shop.stripe_subscriptions import create_stripe_checkout_session

from shop.shop_data import pending_actions, member_history, receipt, get_product_data, all_product_data, \
    get_membership_products, special_product_data
from shop.stripe_event import stripe_callback
from shop.transactions import ship_labaccess_orders
from logging import getLogger

from shop.stripe_subscriptions import SubscriptionType
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
    relation=OrmSingeRelation('images', 'product_id'),
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

service.related_entity_routes(
    path="/product/<int:related_entity_id>/actions",
    entity=product_action_entity,
    relation=OrmSingeRelation('actions', 'product_id'),
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
    relation=OrmSingeRelation('contents', 'transaction_id'),
    permission_list=WEBSHOP,
)


service.related_entity_routes(
    path="/transaction/<int:related_entity_id>/actions",
    entity=transaction_action_entity,
    relation=OrmSingleSingleRelation('actions', TransactionContent, 'transaction_id'),
    permission_list=WEBSHOP,
)


service.related_entity_routes(
    path="/member/<int:related_entity_id>/transactions",
    entity=transaction_entity,
    relation=OrmSingeRelation('member', 'member_id'),
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
def accessy_invite():
    try:
        ensure_accessy_labaccess(member_id=g.user_id)
    except AccessyInvitePreconditionFailed as e:
        raise PreconditionFailed(message=str(e))
    

@service.route("/member/current/subscription", method=POST, permission=USER)
def start_subscription_route(subscription_type=Arg(str, required=True), checkout_session_id=Arg(str, required=False), success_url=Arg(str, required=True)):
    start_subscription(member_id=g.user_id, subscription_type=subscription_type)
    return success_url


@dataclass
class ReloadPage:
    def __init__(self) -> None:
        self.reload = True

@service.route("/member/current/subscription", method=DELETE, permission=USER)
def cancel_subscription_route(subscription_type=Arg(str, required=True), success_url=Arg(str, required=False)):
    try:
        cancel_subscription(member_id=g.user_id, subscription_type=subscription_type)
        return ReloadPage()
    except Exception as e:
        # Don't expose error details to the user
        logger.error(e)
        raise InternalServerError("Failed to cancel subscription")


@service.route("/member/current/stripe_customer_portal", method=GET, permission=PUBLIC)
def open_stripe_customer_portal_route():
    return open_stripe_customer_portal(g.user_id)


@service.route("/member/<int:member_id>/ship_labaccess_orders", method=POST, permission=MEMBER_EDIT)
def ship_labaccess_orders_endpoint(member_id=None):
    try:
        ship_labaccess_orders(member_id, skip_ensure_accessy=True)
        ensure_accessy_labaccess(member_id)  # Always do this, not only when the order is shipped.
    except AccessyInvitePreconditionFailed as e:
        raise PreconditionFailed(message=str(e))


@service.route("/product_data", method=GET, permission=PUBLIC)
def shop_data():
    return all_product_data()


@service.route("/product_data/<int:product_id>", method=GET, permission=PUBLIC)
def product_data(product_id):
    return get_product_data(product_id)


@service.raw_route("/image/<int:image_id>")
def public_image(image_id: int) -> Response:
    try:
        image = db_session.query(ProductImage).filter(ProductImage.id == image_id, ProductImage.deleted_at.is_(None)).one()
    except NoResultFound:
        return send_file("/work/default-product-image.png", mimetype='image/png')

    response = make_response(image.data)
    response.headers.set("Content-Type", image.type)
    response.headers.set("Max-Age", "36000")
    return response


@service.route("/register_page_data", method=GET, permission=PUBLIC)
def register_page_data():
    return {
        "membershipProducts": get_membership_products(),
        "productData": [product_entity.to_obj(p) for p in special_product_data()],
        "discounts": {
            price_level.value: get_discount_fraction_off(price_level).fraction_off for price_level in PriceLevel
        }
    }


@service.route("/pay", method=POST, permission=USER, commit_on_error=True)
def pay_route() -> PartialPayment:
    return pay(request.json, g.user_id)

# Used to just initiate a capture of a payment method via a setup intent
@service.route("/setup_payment_method", method=GET, permission=USER, commit_on_error=True)
def stripe_payment_method_route():
    url = create_stripe_checkout_session(g.user_id, data=request.json)
    return redirect(url)

@service.route("/confirm_payment", method=POST, permission=PUBLIC, commit_on_error=True)
def confirm_payment_route() -> PartialPayment:
    return confirm_stripe_payment_intent(request.json)


@service.route("/register", method=POST, permission=PUBLIC, commit_on_error=True)
def register_route():
    assert request.remote_addr is not None
    return register(request.json, request.remote_addr, request.user_agent.string)

@service.route("/register2", method=POST, permission=PUBLIC, commit_on_error=True)
def register2_route() -> Any:
    assert request.remote_addr is not None
    return register2(request.json, request.remote_addr, request.user_agent.string).to_dict()

@service.route("/stripe_callback", method=POST, permission=PUBLIC, commit_on_error=True)
def stripe_callback_route():
    stripe_callback(request.data, request.headers)

