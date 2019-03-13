from logging import getLogger

from jsonschema import validate, ValidationError
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from core import auth
from membership.views import member_entity
from service.db import db_session
from service.error import NotFound, UnprocessableEntity, BadRequest
from shop.entities import transaction_entity, transaction_content_entity, product_entity, category_entity, \
    product_image_entity
from shop.models import Action, Transaction, Product, ProductCategory, ProductAction
from shop.pay import pay
from shop.schemas import register_schema
from shop.transactions import pending_actions_query

logger = getLogger('makeradmin')


# stripe_signing_secret = os.environ["STRIPE_SIGNING_SECRET"]


def pending_actions(member_id=None):
    query = pending_actions_query(member_id)
    
    return [
        {
            "item": {
                "id": content.id,
                "transaction_id": content.transaction_id,
                "product_id": content.product_id,
                "count": content.count,
                "amount": str(content.amount),
            },
            "action": {
                "id": action_type.id,
                "name": action_type.name,
            },
            "pending_action": {
                "id": action.id,
                "value": action.value,
            },
            "member_id": transaction.member_id,
            "created_at": transaction.created_at.isoformat(),
        } for action, action_type, content, transaction in query
    ]


def member_history(member_id):
    query = (
        db_session
        .query(Transaction)
        .options(joinedload('contents'), joinedload('contents.product'))
        .filter(Transaction.member_id == member_id)
        .order_by(desc(Transaction.id))
    )
    
    return [{
        **transaction_entity.to_obj(transaction),
        'contents': [{
            **transaction_content_entity.to_obj(content),
            'product': product_entity.to_obj(content.product),
        } for content in transaction.contents]
    } for transaction in query.all()]


def receipt(member_id, transaction_id):
    try:
        transaction = db_session.query(Transaction).filter_by(member_id=member_id, id=transaction_id).one()
    except NoResultFound:
        raise NotFound()
    
    return {
        'member': member_entity.to_obj(transaction.member),
        'transaction': transaction_entity.to_obj(transaction),
        'cart': list((product_entity.to_obj(content.product), transaction_content_entity.to_obj(content))
                     for content in transaction.contents)
    }


def all_product_data():
    """ Return all public products and categories. """
    
    query = (
        db_session
        .query(ProductCategory)
        .options(joinedload(ProductCategory.products))
        .filter(Product.deleted_at.is_(None))
        .order_by(ProductCategory.display_order)
    )
    
    return [{
        **category_entity.to_obj(category),
        'items': [{
            **product_entity.to_obj(product),
            'image': product.image or 'default_image.png',
        } for product in sorted(category.products, key=lambda p: p.display_order)]
    } for category in query]
    

def get_product_data(product_id):
    try:
        product = db_session.query(Product).filter_by(id=product_id, deleted_at=None).one()
    except NoResultFound:
        raise NotFound()
    
    images = product.images.filter_by(deleted_at=None)
    
    return {
        "product": product_entity.to_obj(product),
        "images": [product_image_entity.to_obj(image) for image in images],
        "productData": all_product_data(),
    }


def membership_products():
    # Find all products which gives a member membership
    # Note: Assumes a product never contains multiple actions of the same type.
    # If this doesn't hold we will get duplicates of that product in the list.
    query = db_session.query(Product).join(ProductAction).join(Action).filter(Action.name == 'add_membership_days',
                                                                              ProductAction.deleted_at.is_(None),
                                                                              Product.deleted_at.is_(None))
    
    return [{"id": p.id, "name": p.name, "price": float(p.price)} for p in query]


def register_member(data, remote_addr, user_agent):
    if not data:
        raise UnprocessableEntity(message="No data was sent in the request. This is a bug.")
    
    try:
        validate(data, schema=register_schema)
    except ValidationError as e:
        raise UnprocessableEntity(message="Data sent in request not in correct format. This is a bug.")

    products = membership_products()

    purchase = data['purchase']

    cart = purchase['cart']
    if len(cart) != 1:
        raise BadRequest(message="The purchase must contain exactly one item.")
        
    item = cart[0]
    if item['count'] != 1:
        raise BadRequest(message="The purchase must contain exactly one item.")
    
    product_id = item['id']
    if product_id not in (p['id'] for p in products):
        raise BadRequest(message=f"Not allowed to purchase the product with id {product_id} when registring.")

    # This will raise if the creation fails.
    member_id = member_entity.create(data.get('member', {}))['member_id']

    # This will raise if the payment fails.
    transaction, redirect = pay(member_id=member_id, purchase=purchase, activates_member=True)

    # TODO Delete member if payment fails. Make <email, deleted_at> uniquie instead of just email.

    # If the pay succeeded (not same as the payment is completed) and the member does not already exists,
    # the user will be logged in.
    token = auth.force_login(remote_addr, user_agent, member_id)['access_token']

    res =  {
        'transaction_id': transaction.id,
        'token': token,
        'redirect': redirect,
    }
    
    logger.info(res)
    
    return res


# def copy_dict(source: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
#     return {key: source[key] for key in fields if key in source}
# 
# 
# def _fail_transaction(transaction_id: int) -> None:
#     with db.cursor() as cur:
#         affected_rows = cur.execute("UPDATE webshop_transactions AS tt SET tt.status = 'failed' WHERE tt.status = 'pending' AND tt.id = %s", (transaction_id,))
#         if affected_rows != 1:
#             eprint(f"Unable to set transaction {transaction_id} to failed!")
# 
# 
# def fail_transaction(transaction_id: int, error_code: int, reason: str) -> None:
#     _fail_transaction(transaction_id)
#     abort(error_code, reason)
# 
# 
# def _fail_stripe_source(source_id: str) -> None:
#     with db.cursor() as cur:
#         affected_rows = cur.execute(
#             "UPDATE webshop_transactions AS tt INNER JOIN webshop_stripe_pending AS sp ON tt.id = sp.transaction_id SET tt.status = 'failed' WHERE sp.stripe_token = %s and tt.status = 'pending'", (source_id,))
#         if affected_rows != 1:
#             eprint(f"Unable to set status to 'failed' for transaction corresponding to source {source_id}")
# 
# 
# def fail_stripe_source(source_id: str, error_code: int, reason: str) -> None:
#     _fail_stripe_source(source_id)
#     abort(error_code, reason)
# 
# 
# def source_to_transaction_id(source_id: str) -> int:
#     with db.cursor() as cur:
#         cur.execute("SELECT transaction_id FROM webshop_transactions INNER JOIN webshop_stripe_pending ON webshop_transactions.id=webshop_stripe_pending.transaction_id WHERE webshop_stripe_pending.stripe_token=%s", (source_id,))
#         return cur.fetchone()
# 
# 
# def stripe_handle_source_callback(subtype: str, event) -> None:
#     if subtype in ["chargeable", "failed", "canceled"]:
#         source = event.data.object
#         transaction_id = source_to_transaction_id(source.id)
#         if transaction_id is None:
#             logger.info(f"Got callback, but no transaction exists for that token ({source.id}). Ignoring this event (this is usually fine)")
#             return None
# 
#         if subtype == "chargeable":
#             # Asynchronous charge should only be initiated from a 3D Secure source
#             if source.type == 'three_d_secure':
#                 # Payment should happen now
#                 try:
#                     create_stripe_charge(transaction_id, source.id)
#                 except Exception as e:
#                     logger.error(f"Error in create_stripe_charge: {str(e)}. Source '{source.id}' for transaction {transaction_id}")
#             elif source.type == 'card':
#                 # All 'card' type sources that should be charged are handled synchonously, not here.
#                 return None
#             else:
#                 # Unknown source type, log and do nothing
#                 logger.warning(f'Unexpected source type {source.type} in stripe webhook: {source}')
#                 return None
#         else:
#             # Payment failed
#             logger.info("Mark transaction as failed")
#             _fail_transaction(transaction_id)
# 
# 
# def stripe_handle_charge_callback(subtype: str, event) -> None:
#     charge = event.data.object
#     if subtype == 'succeeded':
#         transaction_id = source_to_transaction_id(charge.source.id)
#         if transaction_id is None:
#             abort(400, f"Unknown charge '{charge.id}' succeeded, no transaction found for charge source '{charge.source.id}'!")
#         else:
#             handle_payment_success(transaction_id)
#     elif subtype == 'failed':
#         _fail_stripe_source(charge.source.id)
#         logger.info(f"Charge '{charge.id}' failed with message '{charge.failure_message}'")
#     elif subtype.startswith('dispute'):
#         # todo: log disputes for display in admin frontend.
#         pass
#     elif subtype.startswith('refund'):
#         # todo: log refund for display in admin frontend.
#         # todo: option in frontend to roll back actions.
#         pass
# 
# 
# @instance.route("stripe_callback", methods=["POST"], permission=None)
# @route_helper
# def stripe_callback() -> None:
#     payload = request.data
#     eprint("Headers: " + str(request.headers))
#     sig_header = request.headers['Stripe-Signature']
# 
#     try:
#         event = stripe.Webhook.construct_event(payload, sig_header, stripe_signing_secret)
#     except ValueError as e:
#         # Invalid payload
#         abort(400)
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         abort(400)
# 
#     eprint(f"Received stripe callback of type {event.type}")
#     (event_type, event_subtype) = tuple(event.type.split('.', 1))
#     if event_type == 'source':
#         stripe_handle_source_callback(event_subtype, event)
#     elif event_type == 'charge':
#         stripe_handle_charge_callback(event_subtype, event)
# 
# 
# def _reprocess_stripe_event(event) -> None:
#     try:
#         logger.info(f"Processing stripe event of type {event.type}")
#         (event_type, event_subtype) = tuple(event.type.split('.', 1))
#         if event_type == 'source':
#             stripe_handle_source_callback(event_subtype, event)
#         elif event_type == 'charge':
#             stripe_handle_charge_callback(event_subtype, event)
#     except HTTPException as e:
#         # Catch and ignore all event processing errors
#         pass
# 
# 
# @instance.route("process_stripe_events", methods=["PUT"])
# @route_helper
# def process_stripe_events() -> None:
#     payload = request.get_json() or {}
#     source_id = payload.get('source_id', None)
#     start = payload.get('start', None)
#     logger.info(f"getting stripe events with start {start} and source_id {source_id}")
#     events = stripe.Event.list(created={'gt': start} if start else None)
#     logger.info(f"got {len(events)} events")
#     for event in events.auto_paging_iter():
#         obj = event.get('data', {}).get('object', {})
#         if source_id and source_id in (obj.get('source', {}).get('id'), obj.get('id')) or not source_id:
#             _reprocess_stripe_event(event)
#         else:
#             logger.info(f"skipping event, not matching source_id")
# 
# 
# def handle_payment_success(transaction_id: int) -> None:
#     complete_transaction(transaction_id)
#     transaction = transaction_entity.get(transaction_id)
#     if transaction['status'] != 'completed':
#         eprint(f"handle_payment_success called but transaction marked as '{transaction['status']}', aborting!")
#         return
# 
#     # Check if this transaction is a new member registration
#     if webshop_pending_registrations.list("transaction_id=%s", [transaction_id]):
#         activate_member(transaction["member_id"])
# 
#     eprint("====== Sending receipt email")
#     send_receipt_email(transaction["member_id"], transaction_id)
#     eprint("Payment complete. id: " + str(transaction_id))
# 
# 
# def activate_member(member_id: int) -> None:
#     eprint("====== Activating member")
#     # Make the member not be deleted
#     r = instance.gateway.post(f"membership/member/{member_id}/activate", {})
#     assert r.ok
#     eprint("====== Activated member")
# 
#     send_new_member_email(member_id)
# 
# 
# def send_receipt_email(member_id: int, transaction_id: int) -> None:
#     transaction = transaction_entity.get(transaction_id)
#     items = transaction_content_entity.list("transaction_id=%s", transaction_id)
#     products = [product_entity.get(item["product_id"]) for item in items]
# 
#     r = instance.gateway.get(f"membership/member/{member_id}")
#     assert r.ok
# 
#     member = r.json()["data"]
# 
#     r = instance.gateway.post("messages/message", {
#         "recipients": [
#             {
#                 "type": "member",
#                 "id": member_id
#             },
#         ],
#         "message_type": "email",
#         "title": "Kvitto - Stockholm Makerspace",
#         "description": render_template("receipt_email.html", cart=zip(products, items), transaction=transaction, currency="kr", member=member, public_url=instance.gateway.get_public_url)
#     })
# 
#     if not r.ok:
#         eprint("Failed to send receipt email")
#         eprint(r.text)
# 
# 
# duplicatePurchaseRands: Set[int] = set()
# 
# 
# @instance.route("pay", methods=["POST"], permission='user')
# @route_helper
# def pay_route() -> Dict[str, int]:
#     data = request.get_json()
#     if data is None:
#         raise errors.MissingJson()
# 
#     member_id = int(assert_get(request.headers, "X-User-Id"))
#     return pay(member_id, data)
# 
# 
# @instance.route("product_edit_data/<int:product_id>/", methods=["GET"], permission="webshop_edit")
# @route_helper
# def product_edit_data(product_id: int):
#     _, categories = get_product_data()
# 
#     if product_id:
#         product = product_entity.get(product_id)
# 
#         # Find the ids and names of all actions that this product has
#         with db.cursor() as cur:
#             cur.execute("SELECT webshop_product_actions.id,webshop_actions.id,webshop_actions.name,webshop_product_actions.value"
#                         " FROM webshop_product_actions"
#                         " INNER JOIN webshop_actions ON webshop_product_actions.action_id=webshop_actions.id"
#                         " WHERE webshop_product_actions.product_id=%s AND webshop_product_actions.deleted_at IS NULL", product_id)
#             actions = cur.fetchall()
#             actions = [{
#                 "id": a[0],
#                 "action_id": a[1],
#                 "name": a[2],
#                 "value": a[3],
#             } for a in actions]
# 
#         images = product_image_entity.list("product_id=%s AND deleted_at IS NULL", product_id)
#     else:
#         product = {
#             "category_id": "",
#             "name": "",
#             "description": "",
#             "unit": "",
#             "price": 0.0,
#             "id": "new",
#             "smallest_multiple": 1,
#         }
#         actions = []
#         images = []
# 
#     action_categories = action_entity.list()
# 
#     filters = sorted(product_filters.keys())
# 
#     return {
#         "categories": categories,
#         "product": product,
#         "actions": actions,
#         "filters": filters,
#         "images": images,
#         "action_categories": action_categories,
#     }
# 
# 
#
