from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, Rounded, localcontext
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

from basic_types.enums import PriceLevel
from dataclasses_json import DataClassJsonMixin
from membership.membership import add_membership_days
from membership.models import Member, Span
from messages.message import send_message
from messages.models import MessageTemplate
from multiaccessy.invite import (
    AccessyError,
    LabaccessRequirements,
    check_labaccess_requirements,
    ensure_accessy_labaccess,
)
from service.api_definition import (
    EMPTY_CART,
    INVALID_ITEM_COUNT,
    NEGATIVE_ITEM_COUNT,
    NON_MATCHING_SUMS,
)
from service.config import config
from service.db import db_session, nested_atomic
from service.error import BadRequest, InternalServerError, NotFound
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.sql import func

from shop.email import (
    send_labaccess_extended_email,
    send_membership_updated_email,
    send_new_member_email,
    send_receipt_email,
)
from shop.filters import PRODUCT_FILTERS
from shop.models import (
    Product,
    ProductAction,
    StripePending,
    Transaction,
    TransactionAction,
    TransactionContent,
)
from shop.stripe_constants import MakerspaceMetadataKeys
from shop.stripe_discounts import get_discount_for_product, get_price_level_for_member
from shop.stripe_subscriptions import SubscriptionType, resume_paused_subscription
from shop.stripe_util import convert_to_stripe_amount

# If false, labaccess is synced to accessy once per week
LABACCESS_SHIPS_IMMEDIATELY_ON_PURCHASE = True

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


@dataclass
class SubscriptionStart(DataClassJsonMixin):
    subscription: SubscriptionType
    expected_to_pay_now: Decimal
    expected_to_pay_recurring: Decimal


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
def commit_transaction_to_db(member_id: int, total_amount: Decimal, contents: List[TransactionContent]) -> Transaction:
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

    return transaction


def commit_fail_transaction(transaction: Transaction) -> None:
    transaction.status = Transaction.FAILED
    db_session.add(transaction)
    db_session.flush()


def pending_actions_query(member_id: Optional[int] = None, transaction: Optional[Transaction] = None) -> Any:
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

    if member_id is not None:
        query = query.filter(Transaction.member_id == member_id)
    else:
        # Exclude transactions with member_id set to None (Gift cards)
        query = query.filter(Transaction.member_id.isnot(None))

    return query


def pending_action_value_sum(member_id: int, action_type: str) -> int:
    """
    Sum all pending actions of type action_type for specified member
    """

    return int(
        pending_actions_query(member_id=member_id)
        .filter(TransactionAction.action_type == action_type)
        .with_entities(func.coalesce(func.sum(TransactionAction.value), 0))
        .scalar()
    )


def complete_pending_action(action: TransactionAction) -> None:
    action.status = TransactionAction.COMPLETED
    action.completed_at = datetime.now(timezone.utc)
    db_session.add(action)
    db_session.flush()


def activate_paused_labaccess_subscription(member_id: int, earliest_start_at: datetime) -> None:
    member = db_session.query(Member).get(member_id)
    if member is not None and member.stripe_labaccess_subscription_id is not None:
        resume_paused_subscription(member.member_id, SubscriptionType.LAB, earliest_start_at, test_clock=None)


def ship_add_labaccess_action(
    action: TransactionAction, transaction: Transaction, current_time: datetime, skip_ensure_accessy: bool = False
) -> None:
    days_to_add = action.value
    assert days_to_add is not None
    assert transaction.member_id is not None, "Trying to ship labaccess action for a transaction without a member_id"

    state = check_labaccess_requirements(transaction.member_id)
    if state != LabaccessRequirements.OK:
        logger.info(
            f"skipping ship_add_labaccess_action because member {transaction.member_id} failed check_labaccess_requirements with {state}"
        )
        return

    assert transaction.created_at is not None
    earliest_start_date = max(current_time, transaction.created_at.astimezone(timezone.utc))
    labaccess_end = add_membership_days(
        transaction.member_id,
        Span.LABACCESS,
        days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}",
        # Note: passing created_at here is important during tests which use a simulated time
        earliest_start_date=earliest_start_date.date(),
    ).labaccess_end
    logger.info(f"Adding labaccess ({days_to_add} days) for member {transaction.member_id} until {labaccess_end}")

    assert labaccess_end

    # After a member has been granted labaccess, we want to make sure that their subscription is active.
    # It may already be active, but if it's paused, we want to resume it.
    # Note: passing earliest_start_date here is important during tests which use a simulated time
    activate_paused_labaccess_subscription(transaction.member_id, earliest_start_date)
    complete_pending_action(action)
    send_labaccess_extended_email(transaction.member_id, days_to_add, labaccess_end)
    if not skip_ensure_accessy:
        ensure_accessy_labaccess(member_id=transaction.member_id)


def ship_add_membership_action(action: TransactionAction, transaction: Transaction, current_time: datetime) -> None:
    days_to_add = action.value
    assert days_to_add is not None
    assert transaction.created_at is not None
    assert transaction.member_id is not None, "Trying to ship membership action for a transaction without a member_id"

    membership_end = add_membership_days(
        transaction.member_id,
        Span.MEMBERSHIP,
        days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}",
        # Note: passing created_at here is important during tests which use a simulated time
        earliest_start_date=max(current_time, transaction.created_at.astimezone(timezone.utc)).date(),
    ).membership_end

    assert membership_end

    complete_pending_action(action)
    send_membership_updated_email(transaction.member_id, days_to_add, membership_end)


def send_price_level_email(member: Member) -> None:
    if PriceLevel(member.price_level) != PriceLevel.Normal:
        admin_email = config.get("ADMIN_EMAIL", default="")
        if admin_email == "":
            logger.warning(f"ADMIN_EMAIL not set, cannot send price level email for member {member.member_id}")
        else:
            send_message(MessageTemplate.NEW_LOW_INCOME_MEMBER, member, recipient_email=admin_email)


def activate_member(member: Member) -> None:
    logger.info(f"activating member {member.member_id}")
    member.deleted_at = None
    member.pending_activation = False
    db_session.add(member)
    db_session.flush()
    send_new_member_email(member)
    send_price_level_email(member)


def create_transaction(member_id: int, purchase: Purchase) -> Transaction:
    total_amount, contents = validate_order(member_id, purchase.cart, purchase.expected_sum)
    transaction = commit_transaction_to_db(member_id=member_id, total_amount=total_amount, contents=contents)

    logger.info(f"created transaction {transaction.id}, total_amount={total_amount}, member_id={member_id}")

    return transaction


def complete_transaction(transaction: Transaction) -> None:
    assert transaction.status == Transaction.PENDING

    transaction.status = Transaction.COMPLETED
    db_session.add(transaction)
    db_session.flush()
    logger.info(
        f"completing transaction {transaction.id}, payment confirmed"
        f", sending email receipt to member {transaction.member_id}"
    )
    send_receipt_email(transaction)


def ship_orders(
    ship_add_labaccess: bool = True,
    transaction_filter: Optional[Transaction] = None,
    member_id: Optional[int] = None,
    current_time: Optional[datetime] = None,
) -> None:
    """
    Completes all orders for purchasing lab access and updates existing keys with new dates.
    If a user does not meet requirements for order (for example labaccess needs phone, signed agreement etc), then the order will remain as not completed.
    If transaction is set this is done only for that transaction.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    for action, content, transaction in pending_actions_query(member_id=member_id, transaction=transaction_filter):
        if ship_add_labaccess and action.action_type == ProductAction.ADD_LABACCESS_DAYS:
            try:
                ship_add_labaccess_action(action, transaction, current_time=current_time)
            except AccessyError as e:
                logger.warning(
                    f"failed to ensure accessy labacess, skipping, member (id {transaction.member_id}, number {transaction.member.member_number}) can self service add later: {e}"
                )

        if action.action_type == ProductAction.ADD_MEMBERSHIP_DAYS:
            ship_add_membership_action(action, transaction, current_time=current_time)


def ship_labaccess_orders(
    member_id: Optional[int] = None, skip_ensure_accessy: bool = False, current_time: Optional[datetime] = None
) -> None:
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    for action, content, transaction in pending_actions_query(member_id=member_id):
        if action.action_type == ProductAction.ADD_LABACCESS_DAYS:
            ship_add_labaccess_action(
                action, transaction, skip_ensure_accessy=skip_ensure_accessy, current_time=current_time
            )


@nested_atomic
def payment_success(transaction: Transaction) -> None:
    complete_transaction(transaction)

    member: Member = transaction.member
    if member.pending_activation:
        # Members are activated when they make their first purchase
        activate_member(transaction.member)

    ship_orders(ship_add_labaccess=LABACCESS_SHIPS_IMMEDIATELY_ON_PURCHASE, transaction_filter=transaction)


def process_cart(member_id: int, cart: List[CartItem]) -> Tuple[Decimal, List[TransactionContent]]:
    contents = []

    member = db_session.query(Member).get(member_id)
    if member is None:
        raise NotFound(message=f"Could not find member with id {member_id}.")
    price_level = get_price_level_for_member(member)

    with localcontext() as ctx:
        ctx.clear_flags()
        total_amount = Decimal(0)

        for item in cart:
            try:
                product_id = item.id
                product = db_session.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).one()
            except NoResultFound:
                raise NotFound(message=f"Could not find product with id {product_id}.")

            if product.price < 0:
                raise InternalServerError(log=f"Product {product_id} has a negative price.")

            count = item.count

            if count <= 0:
                raise BadRequest(
                    message=f"Bad product count for product {product_id}.",
                    what=NEGATIVE_ITEM_COUNT,
                )

            if product.get_metadata(MakerspaceMetadataKeys.SUBSCRIPTION_TYPE, None) is not None:
                if count != product.smallest_multiple:
                    raise BadRequest(
                        f"Bad count for subscription product {product_id}. Count must be exactly {product.smallest_multiple}, was {count}.",
                        what=INVALID_ITEM_COUNT,
                    )

            if count % product.smallest_multiple != 0:
                raise BadRequest(
                    f"Bad count for product {product_id}, must be in multiples "
                    f"of {product.smallest_multiple}, was {count}.",
                    what=INVALID_ITEM_COUNT,
                )

            if product.filter:
                PRODUCT_FILTERS[product.filter](item, member_id)

            discount = get_discount_for_product(product, price_level)

            amount = Decimal(product.price) * Decimal(count) * (1 - discount.fraction_off)
            total_amount += amount

            content = TransactionContent(product_id=product_id, count=count, amount=amount)
            contents.append(content)

        if ctx.flags[Rounded]:
            # This can possibly happen with huge values, I suppose they will be caught below anyway but it's good to
            # catch in any case.
            raise InternalServerError("Internal server error", log="Rounding error when calculating cart sum.")

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
