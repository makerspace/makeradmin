from flask import g, request, send_file, make_response
from sqlalchemy.exc import NoResultFound

from multiaccessy.invite import AccessyInvitePreconditionFailed, ensure_accessy_labaccess
from service.api_definition import WEBSHOP, WEBSHOP_EDIT, PUBLIC, GET, USER, POST, Arg, WEBSHOP_ADMIN, MEMBER_EDIT
from service.db import db_session
from service.entity import OrmSingeRelation, OrmSingleSingleRelation
from service.error import PreconditionFailed
from shop import service
from shop.entities import product_image_entity, transaction_content_entity, transaction_entity, \
    transaction_action_entity, product_entity, category_entity, product_action_entity
from shop.models import TransactionContent, ProductImage
from shop.pay import pay, register
<<<<<<< HEAD

# Next two needed?
from shop.stripe_payment_intent import confirm_stripe_payment_intent
from shop.stripe_checkout import create_stripe_checkout_session

from shop.stripe_payment_intent import confirm_stripe_payment_intent
from shop.stripe_checkout import create_stripe_checkout_session

from shop.shop_data import pending_actions, member_history, receipt, get_product_data, all_product_data, \
    get_membership_products
from shop.stripe_event import stripe_callback, process_stripe_events
from shop.stripe_payment_intent import confirm_stripe_payment_intent
from shop.transactions import ship_labaccess_orders

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
def public_image(image_id):
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
    return {"membershipProducts": get_membership_products(), "productData": all_product_data()}

# @service.route("/pay", method=POST, permission=USER, commit_on_error=True)
@service.route("/ship_orders", method=POST, permission=WEBSHOP, commit_on_error=True)
def ship_orders_route():
    ship_orders(ship_add_labaccess=True)


@service.route("/checkout", method=POST, permission=USER, commit_on_error=True)
# @service.route("/pay", method=POST, permission=USER, commit_on_error=True)
def pay_route():
    return create_stripe_checkout_session(request.json, g.user_id)


@service.route("/confirm_payment", method=POST, permission=PUBLIC, commit_on_error=True)
def confirm_payment_route():
    return confirm_stripe_payment_intent(request.json)


@service.route("/register", method=POST, permission=PUBLIC, commit_on_error=True)
def register_route():
    return register(request.json, request.remote_addr, request.user_agent.string)


@service.route("/stripe_callback", method=POST, permission=PUBLIC, commit_on_error=True)
def stripe_callback_route():
    stripe_callback(request.data, request.headers)


@service.route("/process_stripe_events", method=POST, permission=WEBSHOP_ADMIN, commit_on_error=True)
def process_stripe_events_route(start=Arg(str, required=False), source_id=Arg(str, required=False),
                                type=Arg(str, required=False)):
    """ Used to make server fetch stripe events, used for testing since webhook is hard to use. """
    return process_stripe_events(start, source_id, type)

