from decimal import Decimal, localcontext, Rounded
from logging import getLogger

import stripe
from sqlalchemy.orm.exc import NoResultFound
from stripe.error import StripeError, CardError, InvalidRequestError

from core import auth
from membership import member_entity
from service.api_definition import NON_MATCHING_SUMS, EMPTY_CART, NEGATIVE_ITEM_COUNT, INVALID_ITEM_COUNT
from service.config import get_public_url
from service.db import db_session
from service.error import NotFound, InternalServerError, BadRequest
from shop.filters import PRODUCT_FILTERS
from shop.models import Product, Transaction, TransactionContent, PendingRegistration, StripePending, TransactionAction, \
    ProductAction
from shop.api_schemas import validate_data, purchase_schema, register_schema
from shop.stripe_code import STRIPE_SOURCE_TYPE_3D_SECURE, create_stripe_charge, convert_to_stripe_amount, CURRENCY
from shop.transactions import complete_transaction, fail_transaction

logger = getLogger('makeradmin')


class PaymentFailed(BadRequest):
    message = 'Payment failed.'


CARD_3D_SECURE_NOT_SUPPORTED = 'not_supported'

CARD_CHARGABLE = "chargeable"
CARD_FAILED = "failed"
CARD_CONSUMED = "consumed"

CHARGE_SUCCEDED = 'succeeded'


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


def add_transaction_to_db(member_id, total_amount, contents):
    """ Save as new transaction with transaction content in db and return transaction_id. """
    
    transaction = Transaction(member_id=member_id, amount=total_amount, status=Transaction.PENDING)
    
    db_session.add(transaction)
    db_session.flush()

    for content in contents:
        content.transaction_id = transaction.id
        db_session.add(content)
        db_session.flush()
        
        db_session.execute(
            """
            INSERT INTO webshop_transaction_actions (content_id, action_type, value, status)
            SELECT :content_id AS content_id, action_type, SUM(:count * value) AS value, :pending AS status
            FROM webshop_product_actions WHERE product_id=:product_id AND deleted_at IS NULL GROUP BY action_type
            """,
            {'content_id': content.id, 'count': content.count, 'pending': TransactionAction.PENDING,
             'product_id': content.product_id}
        )
    
    return transaction


# TODO Rename.
def handle_card_source(transaction, card_source_id):
    card_source = stripe.Source.retrieve(card_source_id)
    if card_source.type != 'card' or card_source.card.three_d_secure != CARD_3D_SECURE_NOT_SUPPORTED:
        raise InternalServerError(f'Synchronous charges should only be made for cards not supporting 3D Secure.')

    status = card_source.status
    
    if status == CARD_CHARGABLE:
        try:
            charge = create_stripe_charge(transaction, card_source_id)
            if charge.status == CHARGE_SUCCEDED:
                # Avoid delay of feedback to customer, could be skipped and handled when webhook is called.
                complete_transaction(transaction)
            return
            
        except InvalidRequestError as e:
            fail_transaction(transaction)
            if "Amount must convert to at least" in str(e):
                raise PaymentFailed("Paynebt too small total. Least chargable amount is around 5 SEK.")

            raise PaymentFailed(log=f"Stripe charge failed: {str(e)}")
            
        except CardError as e:
            fail_transaction(transaction)
            error = e.json_body.get('error', {})
            raise PaymentFailed(message=error.get("message"), log=f"Stripe charge failed: {str(error)}")
    
        except (Exception, StripeError) as e:
            fail_transaction(transaction)
            raise PaymentFailed(log=f"Stripe charge failed: {str(e)}")
        
    if status == CARD_FAILED:
        fail_transaction(transaction)
        raise PaymentFailed()
    
    if status == CARD_CONSUMED:
        # Not necessarily an error but shouldn't happen.
        fail_transaction(transaction)
        raise InternalServerError(f"Stripe source already marked as 'consumed'.")
    
    fail_transaction(transaction)
    raise InternalServerError(f"Unknown stripe source status '{status}', this is a bug.", log=True)


def handle_three_d_secure_source(transaction, card_source_id, total_amount):
    try:
        stripe_amount = convert_to_stripe_amount(total_amount)
        source = stripe.Source.create(
            amount=stripe_amount,
            currency=CURRENCY,
            type=STRIPE_SOURCE_TYPE_3D_SECURE,
            three_d_secure={'card': card_source_id},
            redirect={'return_url': get_public_url(f"/shop/receipt/{transaction.id}")},
        )
    except InvalidRequestError as e:
        fail_transaction(transaction)
        if "Amount must convert to at least" in str(e):
            raise PaymentFailed("Paynebt too small total. Least chargable amount is around 5 SEK.")

        raise PaymentFailed(log=True)

    # TODO Is this stripe source different?
    db_session.add(StripePending(transaction_id=transaction.id, stripe_token=source.id))
    logger.info(f"created stripe pending for transaction {transaction.id}, source id {source.id}")

    status = source.status
    if status in {"pending", "chargeable"}:
        # Assert 3d secure is pending redirect
        if source.redirect.status not in {'pending', 'not_required'}:
            fail_transaction(transaction)
            raise InternalServerError(log=f"unexpected value for source.redirect.status, '{source.redirect.status}'")
        # Assert 3d secure is pending redirect
        if not source.redirect.url:
            fail_transaction(transaction)
            raise InternalServerError(log=f"invalid value for source.redirect.url, '{source.redirect.url}'")
        # Redirect the user to do the 3D secure confirmation step
        if source.redirect.status == 'pending':
            return source.redirect.url
        
    elif status == "failed":
        fail_transaction(transaction)
        raise PaymentFailed()
    else:
        fail_transaction(transaction)
        raise InternalServerError(log=f"unknown stripe source status '{status}'")

    return None


def get_membership_products():
    # Find all products which gives a member membership
    # Note: Assumes a product never contains multiple actions of the same type.
    # If this doesn't hold we will get duplicates of that product in the list.
    query = (db_session
             .query(Product)
             .join(ProductAction)
             .filter(ProductAction.action_type == ProductAction.ADD_MEMBERSHIP_DAYS,
                     ProductAction.deleted_at.is_(None),
                     Product.deleted_at.is_(None))
    )
    
    return [{"id": p.id, "name": p.name, "price": float(p.price)} for p in query]


def make_purchase(member_id=None, purchase=None, activates_member=False):
    """ Pay using the data in purchase, the purchase structure should be validated according to schema.  """
    
    card_source_id = purchase["stripe_card_source_id"]
    card_3d_secure = purchase["stripe_card_3d_secure"]
    
    total_amount, contents = validate_payment(member_id, purchase["cart"], purchase["expected_sum"])

    transaction = add_transaction_to_db(member_id, total_amount, contents)
    
    if activates_member:
        # Mark this transaction as one that is for registering a member.
        db_session.add(PendingRegistration(transaction_id=transaction.id))

    db_session.add(StripePending(transaction_id=transaction.id, stripe_token=card_source_id))
    db_session.commit()

    logger.info(f"pay card_source_id={card_source_id}, card_3d_secure={card_3d_secure}"
                f", total_amount={total_amount}, transaction_id={transaction.id}")
    
    if card_3d_secure == CARD_3D_SECURE_NOT_SUPPORTED:
        handle_card_source(transaction, card_source_id)
        redirect = None
    else:
        redirect = handle_three_d_secure_source(transaction, card_source_id, total_amount)

    return transaction, redirect
    
    
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
