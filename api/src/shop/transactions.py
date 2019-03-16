from datetime import datetime
from logging import getLogger

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from membership.membership import add_membership_days
from membership.models import Key, LABACCESS
from service.db import db_session
from service.error import InternalServerError
from shop.email import send_key_updated_email, send_membership_updated_email
from shop.models import TransactionAction, TransactionContent, Transaction, PENDING, COMPLETED, FAILED, \
    ADD_LABACCESS_DAYS, ADD_MEMBERSHIP_DAYS

logger = getLogger('makeradmin')


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
        .filter(TransactionAction.status == PENDING)
        .filter(Transaction.status == COMPLETED)
    )

    if member_id:
        query = query.filter(Transaction.member_id == member_id)
        
    return query
    

def complete_pending_action(action):
    action.status = COMPLETED
    action.completed_at = datetime.utcnow()
    db_session.add(action)
    db_session.flush()


def ship_add_labaccess_action(action, transaction):
    days_to_add = action.value

    if not db_session.query(Key).filter(Key.member_id == transaction.member_id, Key.deleted_at.is_(None)).count():
        logger.info(f"skipping ship_add_labaccess_action because member {transaction.member_id} has no key")
        return

    labaccess_end = add_membership_days(
        transaction.member_id, LABACCESS, days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}"
    ).labaccess_end
    
    # TODO BM Can this assert fail too?
    assert labaccess_end
    
    complete_pending_action(action)
    send_key_updated_email(transaction.member_id, days_to_add, labaccess_end)


def ship_add_membership_action(action, transaction):
    days_to_add = action.value

    membership_end = add_membership_days(
        transaction.member_id, LABACCESS, days=days_to_add,
        creation_reason=f"transaction_action_id: {action.id}, transaction_id: {transaction.id}",
        default_start_date=transaction.created_at.date(),
    ).membership_end

    # TODO BM This assert fails when running tests, but then we catch all exceptions... Investigate.
    assert membership_end

    complete_pending_action(action)
    send_membership_updated_email(action.member_id, days_to_add, membership_end)


def ship_orders(ship_add_labaccess=True):
    """
    Completes all orders for purchasing lab access and updates existing keys with new dates.
    If a user has no key yet, then the order will remain as not completed.
    If a user has multiple keys, all of them are updated with new dates.
    """
    for action, content, transaction in pending_actions_query():

        if ship_add_labaccess and action.action == ADD_LABACCESS_DAYS:
            ship_add_labaccess_action(action, transaction)

        if action.action == ADD_MEMBERSHIP_DAYS:
            ship_add_membership_action(action, transaction)


def complete_transaction(transaction):
    if transaction.status == PENDING:
        transaction.status = COMPLETED
        db_session.add(transaction)
        db_session.flush()
        try:
            ship_orders(ship_add_labaccess=False)
        except Exception as e:  # TODO BM Don't catch all here, it is very bad.
            logger.exception(f"failed to ship orders in transaction {transaction.id}, ignoring error")


def fail_transaction(transaction):
    transaction.status = FAILED
    db_session.add(transaction)
    db_session.flush()


def get_source_transaction(source_id):
    try:
        return db_session.query(Transaction).filter(Transaction.stripe_pending.stripe_token == source_id).one()
    except NoResultFound as e:
        return None
    except MultipleResultsFound as e:
        raise InternalServerError(log=f"stripe token {source_id} has multiple transactions, this is a bug") from e



