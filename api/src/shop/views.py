from flask import g, request

from service.api_definition import WEBSHOP, WEBSHOP_EDIT, PUBLIC, GET, USER, POST, SERVICE, Arg
from service.entity import OrmSingeRelation, OrmSingleSingleRelation
from shop import service
from shop.entities import product_image_entity, transaction_content_entity, transaction_entity, \
    transaction_action_entity, product_entity, category_entity, product_action_entity
from shop.models import TransactionContent
from shop.pay import pay, register
from shop.shop_data import pending_actions, member_history, receipt, get_product_data, all_product_data, \
    get_membership_products
from shop.stripe_code import stripe_callback, process_stripe_events, test_stripe_source_event
from shop.transactions import ship_orders

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
    permission_list=PUBLIC,
    permission_read=PUBLIC,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


@service.route("/ship_orders", method=POST, permission=WEBSHOP)
def ship_orders_route():
    ship_orders(ship_add_labaccess=True)


@service.route("/member/current/pending_actions", method=GET, permission=USER)
def pending_actions_for_member():
    return pending_actions(g.user_id)  # TODO BM Fix usages, returned data was changed.


@service.route("/member/current/transactions", method=GET, permission=USER)
def transactions_for_member():
    return member_history(g.user_id)


@service.route("/member/current/receipt/<int:transaction_id>", method=GET, permission=USER)
def receipt_for_member(transaction_id):
    return receipt(g.user_id, transaction_id)


@service.route("/product_data", method=GET, permission=PUBLIC)
def shop_data():
    return all_product_data()


@service.route("/product_data/<int:product_id>", method=GET, permission=PUBLIC)
def product_data(product_id):
    return get_product_data(product_id)


@service.route("/register_page_data", method=GET, permission=PUBLIC)
def register_page_data():
    return {"membershipProducts": get_membership_products(), "productData": all_product_data()}


@service.route("/pay", method=POST, permission=USER)
def pay_route():
    return pay(request.json, g.user_id)


@service.route("/register", method=POST, permission=PUBLIC)
def register_route():
    return register(request.json, request.remote_addr, request.user_agent.string)


@service.route("/stripe_callback", method=POST, permission=PUBLIC)
def stripe_callback_route():
    stripe_callback(request.data, request.headers)


@service.route("/test_stripe_event", method=POST, permission=SERVICE)
def test_stripe_source_event_route():
    """ This endpoint is used for testing only. """
    test_stripe_source_event(request.data)


@service.route("/process_stripe_events", method=POST, permission=SERVICE)
def process_stripe_events_route(start=Arg(str, required=False), source_id=Arg(str, required=False)):
    """ Used to make server fetch stripe events, mainly for testing. """
    process_stripe_events(start, source_id)




