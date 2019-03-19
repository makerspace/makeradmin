from decimal import Decimal, localcontext, Rounded
from logging import getLogger

import stripe
from sqlalchemy.orm.exc import NoResultFound
from stripe.error import StripeError, CardError, InvalidRequestError

from core import auth
from membership import member_entity
from service.api_definition import NON_MATCHING_SUMS, EMPTY_CART, NEGATIVE_ITEM_COUNT, INVALID_ITEM_COUNT
from service.db import db_session
from service.error import NotFound, InternalServerError, BadRequest
from shop.filters import PRODUCT_FILTERS
from shop.models import Product, TransactionContent, ProductAction
from shop.api_schemas import validate_data, purchase_schema, register_schema
from shop.shop_data import get_membership_products
from shop.stripe_code import convert_to_stripe_amount, handle_stripe_source
from shop.transactions import commit_transaction_to_db

logger = getLogger('makeradmin')


def process_cart(member_id, cart):
    contents = []
    with localcontext() as ctx:
        ctx.clear_flags()
        total_amount = Decimal(0)

        for item in cart:
            try:
                product_id = item['id']
                product = db_session.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).one()
            except NoResultFound:
                raise NotFound(message=f"Could not find product with id {product_id}.")
            
            if product.price < 0:
                raise InternalServerError(log=f"Product {product_id} has a negative price.")
            
            count = item['count']
            
            if count <= 0:
                raise BadRequest(message=f"Bad product count for product {product_id}.", what=NEGATIVE_ITEM_COUNT)
            
            if count % product.smallest_multiple != 0:
                raise BadRequest(f"Bad count for product {product_id}, must be in multiples "
                                 f"of {product.smallest_multiple}, was {count}.", what=INVALID_ITEM_COUNT)

            if product.filter:
                PRODUCT_FILTERS[product.filter](cart_item=item, member_id=member_id)

            amount = product.price * count
            total_amount += amount

            content = TransactionContent(product_id=product_id, count=count, amount=amount)
            contents.append(content)

        if ctx.flags[Rounded]:
            # This can possibly happen with huge values, I suppose they will be caught below anyway but it's good to
            # catch in any case.
            raise InternalServerError(log="Rounding error when calculating cart sum.")

    return total_amount, contents


def validate_payment(member_id, cart, expected_amount: Decimal):
    """ Validate that the expected amount matches what in the cart. Returns total_amount and cart items. """
    
    if not cart:
        raise BadRequest(message="No items in cart.", what=EMPTY_CART)

    total_amount, unsaved_contents = process_cart(member_id, cart)

    # Ensure that the frontend hasn't calculated the amount to pay incorrectly
    if abs(total_amount - Decimal(expected_amount)) > Decimal("0.01"):
        raise BadRequest(f"Expected total amount to pay to be {expected_amount} "
                         f"but the cart items actually sum to {total_amount}.",
                         what=NON_MATCHING_SUMS)

    if total_amount > 10000:
        raise BadRequest("Maximum amount is 10000.")

    # Assert that the amount can be converted to a valid stripe amount.
    convert_to_stripe_amount(total_amount)

    return total_amount, unsaved_contents


def make_purchase(member_id=None, purchase=None, activates_member=False):
    """ Pay using the data in purchase, the purchase structure should be validated according to schema.  """
    
    card_source_id = purchase["stripe_card_source_id"]
    card_3d_secure = purchase["stripe_card_3d_secure"]
    
    total_amount, contents = validate_payment(member_id, purchase["cart"], purchase["expected_sum"])

    transaction = commit_transaction_to_db(member_id=member_id, total_amount=total_amount, contents=contents,
                                           stripe_card_source_id=card_source_id, activates_member=activates_member)

    logger.info(f"created transaction {transaction.id},  stripe_card_source_id={card_source_id}"
                f", card_3d_secure={card_3d_secure}, total_amount={total_amount}, member_id={member_id}")
    
    redirect_url = handle_stripe_source(transaction, card_source_id, card_3d_secure)
    
    return transaction, redirect_url
    
    
def pay(data, member_id):
    validate_data(purchase_schema, data or {})

    if member_id <= 0:
        raise BadRequest("You must be a member to purchase materials and tools.")
   
    # This will raise if the payment fails.
    transaction, redirect = make_purchase(member_id=member_id, purchase=data)
    
    return {
        'transaction_id': transaction.id,
        'redirect': redirect,
    }
  

def register(data, remote_addr, user_agent):
    
    validate_data(register_schema, data or {})

    products = get_membership_products()

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

    # This will raise if the creation fails, if it succeeds it will commit the member.
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
