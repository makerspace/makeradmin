import time
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from logging import getLogger
from typing import Dict, List, Optional, Set, Tuple

import stripe
from basic_types.enums import PriceLevel
from membership.models import Member
from service.db import db_session
from service.error import BadRequest, InternalServerError, NotFound
from stripe import InvalidRequestError

from shop.models import Discount, Product
from shop.stripe_constants import CURRENCY, MakerspaceMetadataKeys
from shop.stripe_util import are_metadata_dicts_equivalent, retry


@dataclass
class DiscountOld:
    coupon: Optional[stripe.Coupon]
    fraction_off: Decimal


logger = getLogger("makeradmin")


DISCOUNT_FRACTIONS: Dict[PriceLevel, DiscountOld | None] = {price_level: None for price_level in PriceLevel}


def get_price_level_for_member(member: Member) -> PriceLevel:
    return PriceLevel(member.price_level)


def get_discount_for_product(product: "Product", price_level: PriceLevel) -> DiscountOld:
    """
    Check if this product gets a discount at the given price level, or if it stays at the normal price
    """
    # TODO implement and return Discount instead of the DiscountOld
    if price_level in map(PriceLevel, product.get_metadata(MakerspaceMetadataKeys.ALLOWED_PRICE_LEVELS, [])):
        return get_discount_fraction_off(price_level)
    else:
        return get_discount_fraction_off(PriceLevel.Normal)


def _get_metadata_for_stripe_coupon(makeradmin_discount: Discount) -> Dict[str, str]:
    return {
        MakerspaceMetadataKeys.DISCOUNT_ID.value: makeradmin_discount.id,
    }


def _get_stripe_equivalent_to_duration_for_discount(makeradmin_discount: Discount) -> Tuple[str, int | None]:
    duration_in_months: int | None = None
    if makeradmin_discount.duration == Discount.REPEATING:
        if makeradmin_discount.duration_in_months > 0:
            duration_in_months = makeradmin_discount.duration_in_months
        else:
            raise RuntimeError(
                f"Makeradmin discount with id {makeradmin_discount.id}"
                + f" does not have duration in months > 0,"
                + f"is {makeradmin_discount.duration_in_months}"
            )
    else:
        if makeradmin_discount.duration_in_months is not None:
            raise RuntimeError(
                f"Makeradmin discount with id {makeradmin_discount.id}"
                + f" has duration type {makeradmin_discount.duration}"
                + f", but has duration in months set to {duration_in_months}"
            )

    return makeradmin_discount.duration, duration_in_months


def _get_coupon_applies_to_stripe_product_ids(makeradmin_discount: Discount) -> Dict[str, str]:
    # TODO implement
    # TODO I think this might only be relevant for subscription products?
    # likely related to get_discount_for_product
    db_session.query(Product).outerjoin(DiscountProductMapping, Discount).filter(
        Discount.id == makeradmin_discount.id
    ).all()
    stripe_product_ids = []
    return {"products": stripe_product_ids}


def get_stripe_coupon(makeradmin_discount: Discount) -> stripe.Coupon | None:
    stripe_coupon_id = makeradmin_discount.stripe_coupon_id
    expand = ["applies_to"]
    if stripe_coupon_id is None:
        return None
    try:
        coupon = retry(lambda: stripe.Coupon.retrieve(stripe_coupon_id, expand=expand))
    except InvalidRequestError as e:
        logger.warning(
            f"failed to retrive coupon from stripe for makeradmin discount with id {makeradmin_discount.id}, {e}"
        )
        return None
    if hasattr(coupon, "deleted") and coupon.deleted:
        raise BadRequest(f"Coupon for discount with id {makeradmin_discount.id} has been deleted")
    return coupon


def eq_makeradmin_stripe_coupon(makeradmin_discount: Discount, stripe_coupon: stripe.Coupon) -> bool:
    """Check that the essential parts of the discount in makeradmin and the stripe coupon are equal"""
    assert stripe_coupon.metadata is not None
    assert stripe_coupon.applies_to is not None

    expected_metadata = _get_metadata_for_stripe_coupon(makeradmin_discount)
    stripe_products_coupon_applies_to = _get_coupon_applies_to_stripe_product_ids(makeradmin_discount)
    duration, duration_in_months = _get_stripe_equivalent_to_duration_for_discount(makeradmin_discount)

    applied_products_equal = set(stripe_coupon.applies_to["products"]) == set(
        stripe_products_coupon_applies_to["products"]
    )

    duration_equal = stripe_coupon.duration == duration and stripe_coupon.duration_in_months == duration_in_months

    return (
        are_metadata_dicts_equivalent(stripe_coupon.metadata, expected_metadata)
        and duration_equal
        and applied_products_equal
        and stripe_coupon.percent_off == makeradmin_discount.percent_off
    )


def _create_stripe_coupon(makeradmin_discount: Discount) -> stripe.Coupon:
    if makeradmin_discount.percent_off <= 0 or makeradmin_discount.percent_off > 100:
        raise RuntimeError(
            f"Makeradmin discount, {makeradmin_discount.id}, has invalid percent off value"
            + f", {makeradmin_discount.percent_off}."
        )
    metadata = _get_metadata_for_stripe_coupon(makeradmin_discount)
    stripe_products_coupon_applies_to = _get_coupon_applies_to_stripe_product_ids(makeradmin_discount)
    duration, duration_in_months = _get_stripe_equivalent_to_duration_for_discount(makeradmin_discount)
    stripe_coupon = retry(
        lambda: stripe.Coupon.create(
            name=makeradmin_discount.name,
            percent_off=makeradmin_discount.percent_off,
            duration=duration,
            duration_in_months=duration_in_months,
            currency=CURRENCY,
            applies_to=stripe_products_coupon_applies_to,
            metadata=metadata,
        )
    )
    makeradmin_discount.stripe_coupon_id = stripe_coupon.id
    db_session.flush()
    return stripe_coupon


def get_or_create_stripe_coupon(makeradmin_discount: Discount) -> stripe.Coupon:
    stripe_coupon = get_stripe_coupon(makeradmin_discount) if makeradmin_discount.stripe_coupon_id else None
    if stripe_coupon is None:
        stripe_coupon = _create_stripe_coupon(makeradmin_discount)
    return stripe_coupon


def get_and_sync_stripe_coupon(makeradmin_discount: Discount) -> stripe.Coupon:
    try:
        stripe_coupon = get_or_create_stripe_coupon(makeradmin_discount)
        if not eq_makeradmin_stripe_coupon(makeradmin_discount, stripe_coupon):
            stripe_coupon = replace_stripe_coupon(makeradmin_discount)
        return stripe_coupon
    except Exception as e:
        raise InternalServerError(f"Failed to sync stripe coupon for discount {makeradmin_discount}. Exception {e}")


def replace_stripe_coupon(makeradmin_discount: Discount, stripe_coupon: stripe.Coupon) -> stripe.Coupon:
    """Create a new coupon based on the duration etc in the makeradmin discount to replace the old stripe coupon"""
    if makeradmin_discount.stripe_coupon_id != stripe_coupon.id:
        raise InternalServerError(
            f"The makeradmin discount {makeradmin_discount.id} does not match the stripe coupon {stripe_coupon.id}."
        )
    logger.warning(
        f"Replacing outdated stripe coupon, {stripe_coupon.id}, with new a one for makeradmin discount {makeradmin_discount.id}"
    )
    delete_stripe_coupon(stripe_coupon.id)
    new_stripe_coupon = _create_stripe_coupon(makeradmin_discount)
    if new_stripe_coupon is None:
        raise RuntimeError(
            f"Failed to replace stripe coupon {stripe_coupon.id} for makeradmin discount {makeradmin_discount.id}"
        )
    return new_stripe_coupon


def delete_stripe_coupon(discount_id: int) -> None:
    discount = db_session.query(Discount).get(discount_id)
    if discount is None:
        raise NotFound(f"Unable to find discount with id {discount}")
    stripe_coupon_id = discount.stripe_coupon_id
    if stripe_coupon_id is not None:
        retry(lambda: stripe.Coupon.delete(stripe_coupon_id))

    discount.stripe_coupon_id = None
    db_session.flush()
