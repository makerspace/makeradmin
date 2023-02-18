from logging import getLogger

import stripe
from stripe.error import SignatureVerificationError

from service.error import BadRequest, InternalServerError
from shop.models import Transaction
from shop.stripe_charge import charge_transaction, create_stripe_charge
from shop.stripe_constants import STRIPE_SIGNING_SECRET, Type, Subtype, SourceType
from shop.transactions import get_source_transaction, commit_fail_transaction, PaymentFailed
from membership.membership import add_membership_days
from service.db import db_session
from membership.models import Member
from membership.models import Span
from shop.stripe_checkout import SubscriptionTypes
from datetime import datetime

logger = getLogger('makeradmin')


class IgnoreEvent(Exception): pass


def get_pending_source_transaction(source_id):
    transaction = get_source_transaction(source_id)
    
    if not transaction:
        raise IgnoreEvent(f"no transaction exists for source ({source_id})")
    
    if transaction.status != Transaction.PENDING:
        raise IgnoreEvent(f"transaction {transaction.id} status is {transaction.status}, source event {source_id}")

    return transaction


def stripe_charge_event(subtype, event):
    charge = event.data.object

    transaction = get_pending_source_transaction(charge.payment_method)

    if subtype == Subtype.SUCCEEDED:
        charge_transaction(transaction, charge)
        
    elif subtype == Subtype.FAILED:
        commit_fail_transaction(transaction)
        logger.info(f"charge failed for transaction {transaction.id}, {charge.failure_message}")
        
    elif subtype.startswith(Subtype.DISPUTE_PREFIX):
        pass
    
    elif subtype.startswith(Subtype.REFUND_PREFIX):
        pass


def stripe_source_event(subtype, event):
    source = event.data.object
    
    transaction = get_pending_source_transaction(source.id)

    if subtype == Subtype.CHARGEABLE:

        if source.type == SourceType.THREE_D_SECURE:
            # Charge card and resolve transaction, don't fail transaction on errors as it may be resolved when we get
            # callback again.
            try:
                charge = create_stripe_charge(transaction, source.id)
            except PaymentFailed as e:
                logger.info(f"failing transaction {transaction.id}, permanent error when creating charge: {str(e)}")
                commit_fail_transaction(transaction)
            else:
                charge_transaction(transaction, charge)
        
        elif source.type == SourceType.CARD:
            # Non 3d secure cards should be charged synchronously in payment, not here.
            raise IgnoreEvent(f"transaction {transaction.id} source event of type card is handled synchronously")
        
        else:
            raise InternalServerError(log=f"unexpected source type '{source.type}'"
                                          f" when handling source event: {source}")
        
    elif subtype in (Subtype.FAILED, Subtype.CANCELED):
        logger.info(f"failing transaction {transaction.id} due to source event subtype {subtype}")
        commit_fail_transaction(transaction)
        
    else:
        raise IgnoreEvent(f"source event subtype {subtype} for transaction {transaction.id}")


def stripe_payment_intent_event(subtype, event):
    payment_intent = event.data.object

    transaction = get_pending_source_transaction(payment_intent.id)

    if subtype == Subtype.PAYMENT_FAILED:
        commit_fail_transaction(transaction)
        logger.info(f"failing transaction {transaction.id}, due to error when processing payment")
        
    else:
        raise IgnoreEvent(f"payment_intent event subtype {subtype} for transaction {transaction.id}")

def stripe_invoice_event(subtype : Subtype, event:any):
    #FIXME: In the case of uncollectable subtype, we should probably e-mail the invoice to the member

    if (subtype == Subtype.PAID):
        print(f"Processing paid invoice {event['id']}")
        # Member has paid something and we can now add things accordingly...
        invoice = event["data"]['object']

        for line in invoice["lines"]['data']:
            subscription_id = line['subscription']
            
            # Ignore non-subscription lines in invoices
            if (subscription_id == None):
                continue

            subscription = stripe.Subscription.retrieve(subscription_id)

            # We ignore any items that doesn't contain the right metadata
            if ("makerspace_user_id" not in subscription["metadata"] or "subscription_type" not in subscription["metadata"]):
                print(f'Subscription {subscription_id} does not have metadata indicating an actionable subscription.')
                continue
            member_id = int(subscription["metadata"]["makerspace_user_id"])
            subscription_type = subscription["metadata"]["subscription_type"]

            span_type = None
            if (subscription_type == SubscriptionTypes.LAB):
                span_type = Span.LABACCESS
            elif (subscription_type == SubscriptionTypes.MEMBERSHIP):
                span_type = Span.MEMBERSHIP

            if (span_type is None):
                print(f"Invalid subscription type {subscription_type} paid in invoice {invoice['id']}.")
                continue

            member:Member = db_session.query(Member).get(member_id)
            
            if (subscription_type == SubscriptionTypes.LAB):
                member.stripe_labaccess_subscription_id = subscription_id
            elif (subscription_type == SubscriptionTypes.MEMBERSHIP):
                member.stripe_membership_subscription_id = subscription_id

            end_ts = int(line["period"]["end"])
            start_ts =int(line["period"]["start"])

            # Divide the timespan down to days
            days = round((end_ts-start_ts)/86400)
            try:
                new_memberships = add_membership_days(member_id=member_id, span_type=span_type, days=days,creation_reason=f"Subscription invoice {invoice['id']} paid")
                print(f"New memberships for member {member.member_number}\n{new_memberships}")
            except Exception as e:
                print(f"ERROR: {e}")
        
        db_session.flush()
        return

def stripe_customer_event(event_subtype:str, event:any):

    try:
        subscription = event["data"]["object"]
        meta = subscription["metadata"]
        
        if ("makerspace_user_id" not in meta):
            print(f"Ignoring customer event {event['id']} without correct metadata")
            return 

        member_id = int(meta["makerspace_user_id"])
        member:Member = db_session.query(Member).get(member_id)
        if (event_subtype == Subtype.SUBSCRIPTION_CREATED):
            # We end up here if a schedule starts the subscription
            if (meta['subscription_type'] == SubscriptionTypes.MEMBERSHIP):
                if (member.stripe_membership_subscription_id != None):
                    print(
                        f"WARNING! New subscripton {subscription['id']} will overwrite {member.stripe_membership_subscription_id}")

                member.stripe_membership_subscription_id = subscription['id']
            elif (meta['subscription_type'] == SubscriptionTypes.LAB):
                if (member.stripe_labaccess_subscription_id != None):
                    print(
                        f"WARNING! New subscripton {subscription['id']} will overwrite {member.stripe_labaccess_subscription_id}")
                member.stripe_labaccess_subscription_id = subscription['id']

        elif (event_subtype == Subtype.SUBSCRIPTION_DELETED):
            if (meta["subscription_type"] == SubscriptionTypes.LAB):
                if (member.stripe_labaccess_subscription_id == subscription['id']):
                    member.stripe_labaccess_subscription_id = None
                else:
                    print(f"Ignoring delete notification for subscription {subscription['id']} on {member} since it isn't current. (Current is {member.stripe_labaccess_subscription_id})")
            elif(meta["subscription_type"] == SubscriptionTypes.MEMBERSHIP):
                if (member.stripe_membership_subscription_id == subscription['id']):
                    member.stripe_membership_subscription_id = None
                else:
                    print(f"Ignoring delete notification for subscription {subscription['id']} on {member} since it isn't current. (Current is {member.stripe_membership_subscription_id})")
        db_session.flush()

    except Exception as e:
        print(e)


def stripe_checkout_event(event_subtype:str, event:any):
    if (event_subtype == Subtype.SESSION_COMPLETED):
        # This event is triggered when we go thru the setup intent flow.
        # This typically happens as part of the subscription flow in MakerAdmin but
        # could happen at other times. For now, we capture this event and set
        # the default invoice payment method to the payment method in the setup
        # intent. We might want to consider updating the default source instead.
        checkout_session = event['data']['object']

        # Only setup intents are of our concern. If a checkout from the webshop
        # triggers the event, we should see other modes than setup.
        if (checkout_session['mode'] == 'setup'):
            setup_intent = stripe.SetupIntent.retrieve(checkout_session['setup_intent'])
            if (setup_intent == None):
                print("No setup intent found!")
                return
            payment_method = setup_intent['payment_method']
            customer = setup_intent['customer']
            print(f"Updating default invoice payment method to {payment_method} for customer {customer}")
            stripe.Customer.modify(customer, invoice_settings = {
                    'default_payment_method' : payment_method,
                    },
                    )
    else:
        print(f"Unknown subtype {event_subtype}")

def stripe_event(event):
    logger.info(f"got stripe event of type {event.type} {event['id']}")

    try:
        event_type, event_subtype = event.type.split('.', 1)
        if event_type == Type.SOURCE:
            stripe_source_event(event_subtype, event)
            
        elif event_type == Type.CHARGE:
            stripe_charge_event(event_subtype, event)

        elif event_type == Type.PAYMENT_INTENT:
            stripe_payment_intent_event(event_subtype, event)
        
        elif event_type == Type.INVOICE:
            stripe_invoice_event(event_subtype, event)
        
        elif event_type == Type.CUSTOMER:
            stripe_customer_event(event_subtype, event)
        
        elif event_type == Type.CHECKOUT:
            stripe_checkout_event(event_subtype, event)
        
    
    except IgnoreEvent as e:
        logger.info(f"ignoring event, {str(e)}")


def stripe_callback(data, headers):
    """ Handle stripe event callback. In case of non 200 response stripe will send the same event again (retrying a
    few times), so the code is written to handle that. For example an error that can be assumed to be intermittent
    like a communication error with stripe will not fail or succeed a transaction but just leave it as is. """
    try:
        signature = headers['Stripe-Signature']
        event = stripe.Webhook.construct_event(data, signature, STRIPE_SIGNING_SECRET)
    except (KeyError, SignatureVerificationError) as e:
        raise BadRequest(log=f"failed to process stripe callback: {str(e)}")

    stripe_event(event)


def process_stripe_events(start=None, source_id=None, type=None):
    """ Used to make server fetch stripe events, used for testing since webhook is hard to use. """
    
    def event_filter(event):
        if not source_id:
            return True

        obj = event.data.object

        if source_id == obj.id:
            return True

        try:
            if source_id == obj.three_d_secure.card:
                return True
        except AttributeError:
            pass
            
        try:
            if source_id == obj.object.source.three_d_secure.card:
                return True
        except AttributeError:
            pass
        
        return False
    
    logger.info(f"getting stripe events with start={start}, source_id={source_id}, type={type}")
    events = list(filter(event_filter,
                         stripe.Event.list(created={'gte': start} if start else None,
                                           type=type)))
    event_count = len(events)
    logger.info(f"got {event_count} events")
    for event in events:
        stripe_event(event)
        
    return event_count
