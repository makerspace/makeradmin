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
from shop.pay import make_purchase
from shop.schemas import register_schema, purchase_schema
from shop.transactions import pending_actions_query

logger = getLogger('makeradmin')


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


def pay(data, member_id):
    if not data:
        raise UnprocessableEntity(message="No data was sent in the request. This is a bug.")
    
    try:
        validate(data, schema=purchase_schema)
    except ValidationError as e:
        raise UnprocessableEntity(message="Data sent in request not in correct format. This is a bug.")
    
    # This will raise if the payment fails.
    transaction, redirect = make_purchase(member_id=member_id, purchase=data)
    
    return {
        'transaction_id': transaction.id,
        'redirect': redirect,
    }
    

def register(data, remote_addr, user_agent):
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
    transaction, redirect = make_purchase(member_id=member_id, purchase=purchase, activates_member=True)

    # TODO Delete member if payment fails. Make <email, deleted_at> uniquie instead of just email.

    # If the pay succeeded (not same as the payment is completed) and the member does not already exists,
    # the user will be logged in.
    token = auth.force_login(remote_addr, user_agent, member_id)['access_token']

    return {
        'transaction_id': transaction.id,
        'token': token,
        'redirect': redirect,
    }
