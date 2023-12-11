from logging import getLogger
from typing import Any, Dict, Optional

import stripe

from stripe.error import InvalidRequestError
from shop.stripe_util import retry, are_metadata_dicts_equivalent
from service.db import db_session
from service.error import NotFound, InternalServerError
from membership.models import Member
from shop.stripe_constants import (
    MakerspaceMetadataKeys as MSMetaKeys,
)

logger = getLogger("makeradmin")


def _get_metadata_for_stripe_customer(makeradmin_member: Member) -> Dict[str, str]:
    return {
        MSMetaKeys.PENDING_MEMBER.value: "pending" if makeradmin_member.pending_activation else "",
        MSMetaKeys.USER_ID.value: str(makeradmin_member.member_id),
        MSMetaKeys.MEMBER_NUMBER.value: str(makeradmin_member.member_number),
    }


def get_stripe_customer(makeradmin_member: Member) -> stripe.Customer | None:
    if makeradmin_member.stripe_customer_id is None:
        return None
    try:
        customer = retry(lambda: stripe.Customer.retrieve(makeradmin_member.stripe_customer_id))
    except InvalidRequestError as e:
        logger.warning(
            f"failed to retrive customer from stripe for makeradmin member with id {makeradmin_member.member_id}, {e}"
        )
        return None
    if hasattr(customer, "deleted") and customer.deleted:
        raise InvalidRequestError(f"Customer for member with id {makeradmin_member.member_id} has been deleted")
    return customer


def eq_makeradmin_stripe_customer(makeradmin_member: Member, stripe_customer: stripe.Customer) -> bool:
    """Check that the essential parts of the member in makeradmin and the stripe customer are equal"""
    member_email = makeradmin_member.email.strip()
    expected_metadata = _get_metadata_for_stripe_customer(makeradmin_member)
    return (
        are_metadata_dicts_equivalent(stripe_customer.metadata, expected_metadata)
        and stripe_customer.email == member_email
    )


def _create_stripe_customer(
    makeradmin_member: Member, test_clock: Optional[stripe.test_helpers.TestClock] = None
) -> stripe.Customer:
    expected_metadata = _get_metadata_for_stripe_customer(makeradmin_member)
    stripe_customer = retry(
        lambda: stripe.Customer.create(
            email=makeradmin_member.email.strip(),
            name=f"{makeradmin_member.firstname} {makeradmin_member.lastname}",
            metadata=expected_metadata,
            test_clock=test_clock,
        )
    )
    # Note: Stripe doesn't update its search index of customers immediately,
    # so the new customer may not be visible to stripe.Customer.search for a few seconds.
    # Therefore we always try to find the customer by its ID, that we store in the database
    makeradmin_member.stripe_customer_id = stripe_customer.stripe_id
    db_session.flush()
    return stripe_customer


def get_or_create_stripe_customer(
    makeradmin_member: Member, test_clock: Optional[stripe.test_helpers.TestClock] = None
) -> stripe.Customer:
    stripe_customer = get_stripe_customer(makeradmin_member) if makeradmin_member.stripe_customer_id else None
    if stripe_customer is None:
        stripe_customer = _create_stripe_customer(makeradmin_member, test_clock)
    return stripe_customer


def get_and_sync_stripe_customer(
    makeradmin_member: Member, test_clock: Optional[stripe.test_helpers.TestClock] = None
) -> stripe.Customer:
    try:
        stripe_customer = get_or_create_stripe_customer(makeradmin_member, test_clock)
        if not eq_makeradmin_stripe_customer(makeradmin_member, stripe_customer):
            stripe_customer = update_stripe_customer(makeradmin_member)
        return stripe_customer
    except Exception as e:
        raise InternalServerError(f"Failed to sync stripe customer for member {makeradmin_member}. Exception {e}")


def update_stripe_customer(makeradmin_member: Member) -> stripe.Customer:
    """Update the stripe product to match the makeradmin product"""
    metadata = _get_metadata_for_stripe_customer(makeradmin_member)
    return retry(
        lambda: stripe.Customer.modify(
            makeradmin_member.stripe_customer_id,
            email=makeradmin_member.email.strip(),
            name=f"{makeradmin_member.firstname} {makeradmin_member.lastname}",
            metadata=metadata,
        )
    )


def delete_stripe_customer(member_id: int) -> None:
    member = db_session.query(Member).get(member_id)
    if member is None:
        raise NotFound(f"Unable to find member with id {member_id}")
    if member.stripe_customer_id is not None:
        # Note: This will also delete all subscriptions
        stripe.Customer.delete(member.stripe_customer_id)

    member.stripe_customer_id = None
    db_session.flush()
