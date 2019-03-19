from datetime import datetime
from logging import getLogger

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from membership.membership import add_membership_days
from membership.models import Key, Span
from service.db import db_session
from service.error import InternalServerError, BadRequest
from shop.email import send_key_updated_email, send_membership_updated_email, send_new_member_email, send_receipt_email
from shop.models import TransactionAction, TransactionContent, Transaction, ProductAction, PendingRegistration, \
    StripePending

logger = getLogger('makeradmin')


class PaymentFailed(BadRequest):
    message = 'Payment failed.'


def commit_transaction_to_db(member_id=None, total_amount=None, contents=None, stripe_card_source_id=None,
                             activates_member=False):
    """ Save as new transaction with transaction content in db and return it transaction. """
    
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
    
    if activates_member:
        # TODO Convert this to a product action.
        # Mark this transaction as one that is for registering a member.
        db_session.add(PendingRegistration(transaction_id=transaction.id))

    # TODO Rename stripe pending to TransactionReferences or something (with type).
    db_session.add(StripePending(transaction_id=transaction.id, stripe_token=stripe_card_source_id))
    db_session.commit()
    
    return transaction


def complete_transaction(transaction):
    assert transaction.status == Transaction.PENDING, "TODO BM let's see if this can be not true"
    
    if transaction.status == Transaction.PENDING:
        transaction.status = Transaction.COMPLETED
        db_session.add(transaction)
        db_session.commit()
        try:
            # TODO Investigate this, should we ship before commit, and should we ship just this transaction?
            # TODO Why do we ship all orders?
            ship_orders(ship_add_labaccess=False)
        except Exception as e:  # TODO BM Don't catch all here, it is very bad.
            logger.exception(f"failed to ship orders in transaction {transaction.id}, ignoring error")


def fail_transaction(transaction):
    transaction.status = Transaction.FAILED
    db_session.add(transaction)
    db_session.commit()


# TODO Check code below.


def pending_actions_query(member_id=None):
    """
    Finds every item in a transaction and checks the actions it has, then checks to see if all those actions have
    been completed (and are not deleted). The actions that are valid for a transaction are precisely those that
    existed at the time the transaction was made. Therefore if an action is added to a product in the future,
    that action will *not* be retroactively applied to all existing transactions.
    """
    
    query = (
        db_session
        .query(TransactionAction, TransactionContent, Transaction)
        .join(TransactionAction.content)
        .join(TransactionContent.transaction)
        .filter(TransactionAction.status == TransactionAction.PENDING)
        .filter(Transaction.status == Transaction.COMPLETED)
    )

    if member_id:
        query = query.filter(Transaction.member_id == member_id)
        
    return query
    

def complete_pending_action(action):
    action.status = TransactionAction.COMPLETED
    action.completed_at = datetime.utcnow()
    db_session.add(action)
    db_session.flush()


def ship_add_labaccess_action(action, transaction):
    days_to_add = action.value

    if not db_session.query(Key).filter(Key.member_id == transaction.member_id, Key.deleted_at.is_(None)).count():
        logger.info(f"skipping ship_add_labaccess_action because member {transaction.member_id} has no key")
        return

    labaccess_end = add_membership_days(
        transaction.member_id,
        Span.LABACCESS,
        days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}"
    ).labaccess_end
    
    # TODO BM Can this assert fail too?
    assert labaccess_end
    
    complete_pending_action(action)
    send_key_updated_email(transaction.member_id, days_to_add, labaccess_end)


def ship_add_membership_action(action, transaction):
    days_to_add = action.value

    membership_end = add_membership_days(
        transaction.member_id,
        Span.LABACCESS,
        days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}",
        default_start_date=transaction.created_at.date(),
    ).membership_end

    # TODO BM This assert fails when running tests, but then we catch all exceptions... Investigate.
    assert membership_end

    complete_pending_action(action)
    send_membership_updated_email(action.member_id, days_to_add, membership_end)


def activate_member(member):
    logger.info(f"activating member {member.id}")
    member.deleted_at = None
    db_session.add(member)
    db_session.flush()
    send_new_member_email(member)


def handle_payment_success(transaction):
    complete_transaction(transaction)
    if transaction.status != Transaction.COMPLETED:
        # TODO Is this really needed?
        logger.error(f"wanted to complete transaction but marked as {transaction.status}")
        return
    
    # Check if this transaction is a new member registration.
    if db_session.query(PendingRegistration).filter(PendingRegistration.transaction_id == transaction.id).count():
        activate_member(transaction.member)
        
    logger.info(f"sending receipt email to member {transaction.member_id}, transaction {transaction.id} complete")
    send_receipt_email(transaction)


def ship_orders(ship_add_labaccess=True):
    """
    Completes all orders for purchasing lab access and updates existing keys with new dates.
    If a user has no key yet, then the order will remain as not completed.
    If a user has multiple keys, all of them are updated with new dates.
    """
    for action, content, transaction in pending_actions_query():

        if ship_add_labaccess and action.action_type == ProductAction.ADD_LABACCESS_DAYS:
            ship_add_labaccess_action(action, transaction)

        if action.action_type == ProductAction.ADD_MEMBERSHIP_DAYS:
            ship_add_membership_action(action, transaction)


# TODO Rename when it is not source.
def get_source_transaction(source_id):
    try:
        return db_session.query(Transaction).filter(Transaction.stripe_pending.stripe_token == source_id).one()
    except NoResultFound as e:
        return None
    except MultipleResultsFound as e:
        raise InternalServerError(log=f"stripe token {source_id} has multiple transactions, this is a bug") from e


