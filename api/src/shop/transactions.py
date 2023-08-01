from dataclasses import dataclass
from decimal import localcontext, Decimal, Rounded
from datetime import datetime
from logging import getLogger
from typing import List, Tuple
from dataclasses_json import DataClassJsonMixin

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql import func


from membership.membership import add_membership_days
from membership.models import Key, Span
from multiaccessy.invite import (
    ensure_accessy_labaccess,
    AccessyError,
    check_labaccess_requirements,
    LabaccessRequirements,
)
from service.api_definition import (
    NEGATIVE_ITEM_COUNT,
    INVALID_ITEM_COUNT,
    EMPTY_CART,
    NON_MATCHING_SUMS,
)
from service.db import db_session, nested_atomic
from service.error import InternalServerError, BadRequest, NotFound
from shop.email import (
    send_labaccess_extended_email,
    send_membership_updated_email,
    send_new_member_email,
    send_receipt_email,
)
from shop.filters import PRODUCT_FILTERS
from shop.models import (
    TransactionAction,
    TransactionContent,
    Transaction,
    ProductAction,
    PendingRegistration,
    StripePending,
    Product,
)
from shop.stripe_util import convert_to_stripe_amount

logger = getLogger("makeradmin")


class PaymentFailed(BadRequest):
    message = "Payment failed."


@dataclass
class CartItem(DataClassJsonMixin):
    id: int
    count: int


@dataclass
class Purchase(DataClassJsonMixin):
    cart: List[CartItem]
    expected_sum: str
    stripe_payment_method_id: str
    transaction_id: Optional[int] = None


def get_source_transaction(source_id: str) -> Optional[Transaction]:
    try:
        return (
            db_session.query(Transaction)
            .filter(Transaction.stripe_pending.any(StripePending.stripe_token == source_id))
            .with_for_update()
            .one()
        )
    except NoResultFound as e:
        return None
    except MultipleResultsFound as e:
        raise InternalServerError(log=f"stripe token {source_id} has multiple transactions, this is a bug") from e


@nested_atomic
def commit_transaction_to_db(
    member_id=None,
    total_amount=None,
    contents=None,
    activates_member=False,
) -> Transaction:
    """Save as new transaction with transaction content in db and return it transaction."""

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
            {
                "content_id": content.id,
                "count": content.count,
                "pending": TransactionAction.PENDING,
                "product_id": content.product_id,
            },
        )

    if activates_member:
        # Mark this transaction as one that is for registering a member.
        db_session.add(PendingRegistration(transaction_id=transaction.id))

    return transaction


def commit_fail_transaction(transaction):
    transaction.status = Transaction.FAILED
    db_session.add(transaction)
    db_session.commit()


def pending_actions_query(member_id=None, transaction=None):
    """
    Finds every item in a transaction and checks the actions it has, then checks to see if all those actions have
    been completed (and are not deleted). The actions that are valid for a transaction are precisely those that
    existed at the time the transaction was made. Therefore if an action is added to a product in the future,
    that action will *not* be retroactively applied to all existing transactions.
    """

    query = (
        db_session.query(TransactionAction, TransactionContent, Transaction)
        .join(TransactionAction.content)
        .join(TransactionContent.transaction)
        .filter(TransactionAction.status == TransactionAction.PENDING)
        .filter(Transaction.status == Transaction.COMPLETED)
    )

    if transaction:
        query = query.filter(Transaction.id == transaction.id)

    if member_id:
        query = query.filter(Transaction.member_id == member_id)

    return query


def pending_action_value_sum(member_id, action_type):
    """
    Sum all pending actions of type action_type for specified member
    """

    return (
        pending_actions_query(member_id=member_id)
        .filter(TransactionAction.action_type == action_type)
        .with_entities(func.coalesce(func.sum(TransactionAction.value), 0))
        .scalar()
    )


def complete_pending_action(action):
    action.status = TransactionAction.COMPLETED
    action.completed_at = datetime.utcnow()
    db_session.add(action)
    db_session.flush()


def ship_add_labaccess_action(action, transaction, skip_ensure_accessy=False):
    days_to_add = action.value

    state = check_labaccess_requirements(transaction.member_id)
    if state != LabaccessRequirements.OK:
        logger.info(
            f"skipping ship_add_labaccess_action because member {transaction.member_id} failed check_labaccess_requirements with {state}"
        )
        return

    labaccess_end = add_membership_days(
        transaction.member_id,
        Span.LABACCESS,
        days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}",
    ).labaccess_end

    assert labaccess_end

    complete_pending_action(action)
    send_labaccess_extended_email(transaction.member_id, days_to_add, labaccess_end)
    if not skip_ensure_accessy:
        ensure_accessy_labaccess(member_id=transaction.member_id)


def ship_add_membership_action(action, transaction):
    days_to_add = action.value

    membership_end = add_membership_days(
        transaction.member_id,
        Span.MEMBERSHIP,
        days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}",
        default_start_date=transaction.created_at.date(),
    ).membership_end

    assert membership_end

    complete_pending_action(action)
    send_membership_updated_email(transaction.member_id, days_to_add, membership_end)


def activate_member(member):
    logger.info(f"activating member {member.member_id}")
    member.deleted_at = None
    db_session.add(member)
    db_session.flush()
    send_new_member_email(member)


def create_transaction(
    member_id: int, purchase: Purchase, activates_member: bool
) -> Transaction:
    total_amount, contents = validate_order(member_id, purchase.cart, purchase.expected_sum)

    transaction = commit_transaction_to_db(
        member_id=member_id,
        total_amount=total_amount,
        contents=contents,
        activates_member=activates_member,
    )

    logger.info(
        f"created transaction {transaction.id}, total_amount={total_amount}, member_id={member_id}"
    )

    return transaction


def complete_transaction(transaction):
    assert transaction.status == Transaction.PENDING

    transaction.status = Transaction.COMPLETED
    db_session.add(transaction)
    db_session.flush()
    logger.info(
        f"completing transaction {transaction.id}, payment confirmed"
        f", sending email receipt to member {transaction.member_id}"
    )
    send_receipt_email(transaction)


def ship_orders(ship_add_labaccess=True, transaction=None):
    """
    Completes all orders for purchasing lab access and updates existing keys with new dates.
    If a user does not meet requirements for order (for example labaccess needs phone, signed agreement etc), then the order will remain as not completed.
    If transaction is set this is done only for that transaction.
    """

    for action, content, transaction in pending_actions_query(transaction=transaction):
        if (
            ship_add_labaccess
            and action.action_type == ProductAction.ADD_LABACCESS_DAYS
        ):
            try:
                ship_add_labaccess_action(action, transaction)
            except AccessyError as e:
                logger.warning(
                    f"failed to ensure accessy labacess, skipping, member (id {transaction.member_id}, number {transaction.member.member_number}) can self service add later: {e}"
                )

        if action.action_type == ProductAction.ADD_MEMBERSHIP_DAYS:
            ship_add_membership_action(action, transaction)


def ship_labaccess_orders(member_id=None, skip_ensure_accessy=False):
    for action, content, transaction in pending_actions_query(member_id=member_id):
        if action.action_type == ProductAction.ADD_LABACCESS_DAYS:
            ship_add_labaccess_action(
                action, transaction, skip_ensure_accessy=skip_ensure_accessy
            )


@nested_atomic
def payment_success(transaction):
    complete_transaction(transaction)
    ship_orders(ship_add_labaccess=False, transaction=transaction)

    if (
        db_session.query(PendingRegistration)
        .filter(PendingRegistration.transaction_id == transaction.id)
        .count()
    ):
        activate_member(transaction.member)


def process_cart(
    member_id: int, cart: List[CartItem]
) -> Tuple[Decimal, List[TransactionContent]]:
    contents = []
    with localcontext() as ctx:
        ctx.clear_flags()
        total_amount = Decimal(0)

        for item in cart:
            try:
                product_id = item.id
                product = (
                    db_session.query(Product)
                    .filter(Product.id == product_id, Product.deleted_at.is_(None))
                    .one()
                )
            except NoResultFound:
                raise NotFound(message=f"Could not find product with id {product_id}.")

            if product.price < 0:
                raise InternalServerError(
                    log=f"Product {product_id} has a negative price."
                )

            count = item.count

            if count <= 0:
                raise BadRequest(
                    message=f"Bad product count for product {product_id}.",
                    what=NEGATIVE_ITEM_COUNT,
                )

            if count % product.smallest_multiple != 0:
                raise BadRequest(
                    f"Bad count for product {product_id}, must be in multiples "
                    f"of {product.smallest_multiple}, was {count}.",
                    what=INVALID_ITEM_COUNT,
                )

            if product.filter:
                PRODUCT_FILTERS[product.filter](item, member_id)

            amount = product.price * count
            total_amount += amount

            content = TransactionContent(
                product_id=product_id, count=count, amount=amount
            )
            contents.append(content)

        if ctx.flags[Rounded]:
            # This can possibly happen with huge values, I suppose they will be caught below anyway but it's good to
            # catch in any case.
            raise InternalServerError(log="Rounding error when calculating cart sum.")

    return total_amount, contents


def validate_order(
    member_id: int, cart: List[CartItem], expected_amount: str
) -> Tuple[Decimal, List[TransactionContent]]:
    """Validate that the expected amount matches what in the cart. Returns total_amount and cart items."""

    if not cart:
        raise BadRequest(message="No items in cart.", what=EMPTY_CART)

    total_amount, unsaved_contents = process_cart(member_id, cart)

    # Ensure that the frontend hasn't calculated the amount to pay incorrectly
    if abs(total_amount - Decimal(expected_amount)) > Decimal("0.01"):
        raise BadRequest(
            f"Expected total amount to pay to be {expected_amount} "
            f"but the cart items actually sum to {total_amount}.",
            what=NON_MATCHING_SUMS,
        )

    if total_amount < 5:
        raise BadRequest("Total amount too small, must be at least 5 SEK.")

    if total_amount > 10000:
        raise BadRequest("Maximum amount is 10 000 SEK.")

    # Assert that the amount can be converted to a valid stripe amount.
    convert_to_stripe_amount(total_amount)

    return total_amount, unsaved_contents
