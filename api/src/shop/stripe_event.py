from decimal import Decimal
from logging import getLogger
from typing import Any, Dict, List, Optional

import stripe
from stripe.error import SignatureVerificationError
from datetime import timezone
from shop import stripe_subscriptions
import shop.transactions
from shop.stripe_util import event_semantic_time

from service.error import BadRequest, InternalServerError
from shop.models import (
    ProductAction,
    Transaction,
    TransactionAction,
    TransactionContent,
)
from shop.stripe_charge import charge_transaction, create_stripe_charge
from shop.stripe_constants import (
    STRIPE_SIGNING_SECRET,
    MakerspaceMetadataKeys,
    Type,
    Subtype,
    SourceType,
)
from shop.transactions import (
    get_source_transaction,
    commit_fail_transaction,
    PaymentFailed,
)
from membership.membership import add_membership_days
from service.db import db_session
from membership.models import Member
from membership.models import Span
from shop.stripe_subscriptions import get_subscription_product, SubscriptionType
from datetime import datetime

logger = getLogger("makeradmin")


class IgnoreEvent(Exception):
    pass


def get_pending_source_transaction(source_id: str) -> Transaction:
    transaction = get_source_transaction(source_id)

    if not transaction:
        raise IgnoreEvent(f"no transaction exists for source ({source_id})")

    if transaction.status != Transaction.PENDING:
        raise IgnoreEvent(
            f"transaction {transaction.id} status is {transaction.status}, source event {source_id}"
        )

    return transaction


def stripe_charge_event(subtype: Subtype, event: stripe.Event) -> None:
    charge = event.data.object

    transaction = get_pending_source_transaction(charge.payment_method)

    if subtype == Subtype.SUCCEEDED:
        charge_transaction(transaction, charge)

    elif subtype == Subtype.FAILED:
        commit_fail_transaction(transaction)
        logger.info(
            f"charge failed for transaction {transaction.id}, {charge.failure_message}"
        )


def stripe_source_event(subtype: Subtype, event: stripe.Event) -> None:
    source = event.data.object

    transaction = get_pending_source_transaction(source.id)

    if subtype == Subtype.CHARGEABLE:

        if SourceType(source.type) == SourceType.THREE_D_SECURE:
            # Charge card and resolve transaction, don't fail transaction on errors as it may be resolved when we get
            # callback again.
            try:
                charge = create_stripe_charge(transaction, source.id)
            except PaymentFailed as e:
                logger.info(
                    f"failing transaction {transaction.id}, permanent error when creating charge: {str(e)}"
                )
                commit_fail_transaction(transaction)
            else:
                charge_transaction(transaction, charge)

        elif source.type == SourceType.CARD:
            # Non 3d secure cards should be charged synchronously in payment, not here.
            raise IgnoreEvent(
                f"transaction {transaction.id} source event of type card is handled synchronously"
            )

        else:
            raise InternalServerError(
                log=f"unexpected source type '{source.type}'"
                f" when handling source event: {source}"
            )

    elif subtype in (Subtype.FAILED, Subtype.CANCELED):
        logger.info(
            f"failing transaction {transaction.id} due to source event subtype {subtype}"
        )
        commit_fail_transaction(transaction)

    else:
        raise IgnoreEvent(
            f"source event subtype {subtype} for transaction {transaction.id}"
        )


def stripe_payment_intent_event(subtype: Subtype, event: stripe.Event) -> None:
    payment_intent = event.data.object

    transaction = get_pending_source_transaction(payment_intent.id)

    if subtype == Subtype.PAYMENT_FAILED:
        commit_fail_transaction(transaction)
        logger.info(
            f"failing transaction {transaction.id}, due to error when processing payment"
        )

    else:
        raise IgnoreEvent(
            f"payment_intent event subtype {subtype} for transaction {transaction.id}"
        )


def stripe_invoice_event(
    subtype: Subtype, event: stripe.Event, current_time: datetime
) -> None:
    # FIXME: In the case of uncollectable subtype, we should probably e-mail the invoice to the member

    if subtype == Subtype.PAID:
        logger.info(f"Processing paid invoice {event['id']}")
        # Member has paid something and we can now add things accordingly...
        invoice = event["data"]["object"]
        # print(invoice)
        transaction_ids: List[int] = []

        for line in invoice["lines"]["data"]:
            metadata: Dict[str, str] = line["metadata"]

            try:
                member_id = int(metadata[MakerspaceMetadataKeys.USER_ID.value])
                subscription_type = SubscriptionType(
                    metadata[MakerspaceMetadataKeys.SUBSCRIPTION_TYPE.value]
                )
            except KeyError as e:
                # We ignore any items that doesn't contain the right metadata
                logger.error(
                    f"Invoice {invoice.id} does not have metadata indicating an actionable subscription: {e}"
                )
                logger.error(invoice)
                continue
            except Exception as e:
                logger.error(f"Unexpected error reading invoice metadata: {e}")
                continue

            member: Optional[Member] = db_session.query(Member).get(member_id)
            if member is None:
                logger.error(
                    f"Ignoring invoice which contains subscription for non-existing member (id={member_id})."
                )
                continue

            end_ts = int(line["period"]["end"])
            start_ts = int(line["period"]["start"])

            # Divide the timespan down to days
            days = round((end_ts - start_ts) / 86400)

            product = get_subscription_product(subscription_type)
            amount = Decimal(line["amount"]) / 100
            transaction = Transaction(
                member_id=member_id,
                amount=amount,
                status=Transaction.COMPLETED,
                # This created_at time is important, as any membership days that are added
                # will not be added before this time.
                # It is important that we set this explicitly instead of using the default (current time),
                # because when tests are running we might be using a simulated time.
                created_at=current_time,
            )
            db_session.add(transaction)
            # We need to flush to get the id of the transaction
            db_session.flush()
            content = TransactionContent(
                transaction_id=transaction.id,
                product_id=product.id,
                count=1,
                amount=amount,
            )
            db_session.add(content)
            db_session.flush()
            db_session.add(
                TransactionAction(
                    content_id=content.id,
                    action_type=ProductAction.ADD_LABACCESS_DAYS
                    if subscription_type == SubscriptionType.LAB
                    else ProductAction.ADD_MEMBERSHIP_DAYS,
                    value=days,
                    status=TransactionAction.PENDING,
                )
            )
            db_session.flush()

            transaction_ids.append(transaction.id)

            # Ship the transaction.
            # This will add membership and labaccess days to the member.
            # It will also send out an email to the member.
            # Unless, of course, the member has not signed the agreement or is failing some other requirements.
            # In that case the transaction actions will stay pending.
            shop.transactions.ship_orders(True, transaction, current_time=current_time)

            # If this is a labaccess subscription, the subscription is immediately paused after the first invoice
            # until the user has signed the labaccess agreement.
            # This allows us to collect the first payment (which will typically be 2 months for the binding period),
            # which creates an incentive for the user to actually go and join this makerspace thingy.
            # A few members will never end up signing the agreement, but we can't do anything about that.
            if (
                subscription_type == SubscriptionType.LAB
                and member.labaccess_agreement_at is None
            ):
                stripe_subscriptions.pause_subscription(
                    member_id, SubscriptionType.LAB, test_clock=None
                )

        db_session.commit()

        if len(transaction_ids) > 0:
            # Attach a makerspace transaction id to the stripe invoice item.
            # This is nice to have in the future if we need to match them somehow.
            # In the vast majority of all cases, this will just contain a single transaction id.
            stripe.Invoice.modify(
                sid=invoice["id"],
                metadata={
                    MakerspaceMetadataKeys.TRANSACTION_IDS.value: ",".join(
                        [str(x) for x in transaction_ids]
                    ),
                },
            )

        return
    elif subtype == Subtype.PAYMENT_FAILED:
        # The user will be notified by Stripe if this happens.
        # This can be configured at https://dashboard.stripe.com/settings/billing/automatic
        # It should also be configured to automatically cancel the subscription after some failed attempts.
        pass


def stripe_customer_event(event_subtype: Subtype, event: stripe.Event) -> None:
    try:
        meta = event["data"]["object"]["metadata"]

        if MakerspaceMetadataKeys.USER_ID.value not in meta:
            logger.warning(
                f"Ignoring customer event {event['id']} without correct metadata"
            )
            return

        member_id = int(meta[MakerspaceMetadataKeys.USER_ID.value])
        member = db_session.query(Member).get(member_id)
        if member is None:
            logger.warning(
                f"Ignoring customer event {event['id']} for non-existing member (id={member_id})."
            )
            return

        if event_subtype in (
            Subtype.SUBSCRIPTION_CREATED,
            Subtype.SUBSCRIPTION_UPDATED,
            Subtype.SUBSCRIPTION_DELETED,
        ):
            subscription = event["data"]["object"]
            subscription_type = SubscriptionType(
                meta[MakerspaceMetadataKeys.SUBSCRIPTION_TYPE.value]
            )
            subscription_id = subscription["id"]

            if event_subtype == Subtype.SUBSCRIPTION_CREATED:
                logger.info(
                    f"Created stripe {subscription_type.name} subscription {subscription_id} for makerspace member {member.member_number}"
                )
            elif event_subtype == Subtype.SUBSCRIPTION_DELETED:
                logger.info(
                    f"Deleted stripe {subscription_type.name} subscription {subscription_id} for makerspace member {member.member_number}"
                )
            elif event_subtype == Subtype.SUBSCRIPTION_UPDATED:
                logger.info(
                    f"Updated stripe {subscription_type.name} subscription {subscription_id} for makerspace member {member.member_number}"
                )

            current_subscription_id = (
                member.stripe_labaccess_subscription_id
                if subscription_type == SubscriptionType.LAB
                else member.stripe_membership_subscription_id
            )

            if event_subtype == Subtype.SUBSCRIPTION_CREATED:
                if current_subscription_id is not None:
                    logger.warning(
                        f"WARNING! New {subscription_type.name} subscription {subscription_id} will overwrite {current_subscription_id}"
                    )

                # We end up here if a schedule starts the subscription
                if subscription_type == SubscriptionType.MEMBERSHIP:
                    member.stripe_membership_subscription_id = subscription_id
                elif subscription_type == SubscriptionType.LAB:
                    member.stripe_labaccess_subscription_id = subscription_id
                else:
                    assert False
            elif event_subtype == Subtype.SUBSCRIPTION_DELETED:
                is_current = current_subscription_id == subscription_id
                if is_current:
                    if subscription_type == SubscriptionType.LAB:
                        member.stripe_labaccess_subscription_id = None
                    elif subscription_type == SubscriptionType.MEMBERSHIP:
                        member.stripe_membership_subscription_id = None
                    else:
                        assert False
                else:
                    logger.warning(
                        f"Ignoring delete notification for {subscription_type.name} subscription {subscription_id} on {member.member_number} since it isn't current. (Current is {current_subscription_id})"
                    )

            db_session.commit()
        else:
            if event_subtype == Subtype.CREATED:
                logger.info(
                    f"Created stripe customer for makerspace member {member.member_number}"
                )
            elif event_subtype == Subtype.UPDATED:
                logger.info(
                    f"Updated stripe customer for makerspace member {member.member_number}"
                )

    except Exception as e:
        logger.error(e)


def stripe_subscription_schedule_event(
    event_subtype: Subtype, event: stripe.Event
) -> None:
    subscription = event["data"]["object"]
    meta = subscription["metadata"]

    if MakerspaceMetadataKeys.USER_ID.value not in meta:
        logger.error(
            f"Ignoring subscription schedule event {event['id']} without correct metadata"
        )
        return

    member_id = int(meta[MakerspaceMetadataKeys.USER_ID.value])
    member: Optional[Member] = db_session.query(Member).get(member_id)
    if member is None:
        logger.warning(
            f"Ignoring subscription schedule event {event['id']} for unknown member {member_id}"
        )
        return

    subscription_type = SubscriptionType(
        meta[MakerspaceMetadataKeys.SUBSCRIPTION_TYPE.value]
    )
    current_subscription_id = (
        member.stripe_labaccess_subscription_id
        if subscription_type == SubscriptionType.LAB
        else member.stripe_membership_subscription_id
    )
    subscription_id = subscription["id"]

    if event_subtype == Subtype.RELEASED:
        # This can happen if we cancel a scheduled subscription before it starts,
        # and it also happens when an active subscription is cancelled.
        is_current = current_subscription_id == subscription_id
        if is_current:
            logger.info(
                f"Removed scheduled stripe subscription for makerspace member {member.member_number}"
            )
            if subscription_type == SubscriptionType.LAB:
                member.stripe_labaccess_subscription_id = None
            elif subscription_type == SubscriptionType.MEMBERSHIP:
                member.stripe_membership_subscription_id = None
            else:
                assert False
        else:
            logger.warning(
                f"Ignoring delete notification for scheduled {subscription_type} subscription {subscription_id} on {member.member_number} since it isn't current. (Current is {current_subscription_id})"
            )


def stripe_checkout_event(event_subtype: Subtype, event: stripe.Event) -> None:
    if event_subtype == Subtype.SESSION_COMPLETED:
        # This event is triggered when we go thru the setup intent flow.
        # This typically happens as part of the subscription flow in MakerAdmin but
        # could happen at other times. For now, we capture this event and set
        # the default invoice payment method to the payment method in the setup
        # intent. We might want to consider updating the default source instead.
        checkout_session = event["data"]["object"]

        # Only setup intents are of our concern. If a checkout from the webshop
        # triggers the event, we should see other modes than setup.
        if checkout_session["mode"] == "setup":
            setup_intent = stripe.SetupIntent.retrieve(checkout_session["setup_intent"])
            if setup_intent == None:
                print("No setup intent found!")
                return
            payment_method = setup_intent["payment_method"]
            customer = setup_intent["customer"]
            print(
                f"Updating default invoice payment method to {payment_method} for customer {customer}"
            )
            stripe.Customer.modify(
                customer,
                invoice_settings={
                    "default_payment_method": payment_method,
                },
            )
    else:
        logger.warning(f"Unknown subtype {event_subtype}")


def stripe_event(event: stripe.Event, current_time: datetime) -> None:
    event_time = event_semantic_time(event)
    logger.info("")
    logger.info(f"Stripe Event: {event.type:<34} {event_time}")

    try:
        event_type_s, event_subtype_s = event.type.split(".", 1)
        try:
            event_type = Type(event_type_s)
            event_subtype = Subtype(event_subtype_s)
        except:
            raise IgnoreEvent(f"unknown event type {event.type}")

        if event_type == Type.SOURCE:
            stripe_source_event(event_subtype, event)

        elif event_type == Type.CHARGE:
            stripe_charge_event(event_subtype, event)

        elif event_type == Type.PAYMENT_INTENT:
            stripe_payment_intent_event(event_subtype, event)

        elif event_type == Type.INVOICE:
            stripe_invoice_event(event_subtype, event, current_time)

        elif event_type == Type.CUSTOMER:
            stripe_customer_event(event_subtype, event)

        elif event_type == Type.CHECKOUT:
            stripe_checkout_event(event_subtype, event)
        elif event_type == Type.SUBSCRIPTION_SCHEDULE:
            stripe_subscription_schedule_event(event_subtype, event)
        else:
            logger.info(f"ignoring unknown event type: {str(event.type)}")

    except IgnoreEvent as e:
        logger.info(f"ignoring event, {str(e)}")


def stripe_callback(data: Any, headers: Dict[str, Any]) -> None:
    """Handle stripe event callback. In case of non 200 response stripe will send the same event again (retrying a
    few times), so the code is written to handle that. For example an error that can be assumed to be intermittent
    like a communication error with stripe will not fail or succeed a transaction but just leave it as is."""
    try:
        signature = headers["Stripe-Signature"]
        event = stripe.Webhook.construct_event(data, signature, STRIPE_SIGNING_SECRET)
    except (KeyError, SignatureVerificationError) as e:
        raise BadRequest(log=f"failed to process stripe callback: {str(e)}")

    stripe_event(event, current_time=datetime.now(timezone.utc))
