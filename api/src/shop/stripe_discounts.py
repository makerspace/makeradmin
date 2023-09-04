from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import time
from typing import TYPE_CHECKING, Dict, List, Optional
import stripe
from shop.stripe_util import retry
from membership.enums import PriceLevel

from shop.stripe_constants import MakerspaceMetadataKeys
if TYPE_CHECKING:
    from membership.models import Member
    from shop.models import Product

@dataclass
class Discount:
    coupon: Optional[stripe.Coupon]
    fraction_off: Decimal

DISCOUNT_FRACTIONS: Optional[Dict[PriceLevel, Discount]] = None

def get_price_level_for_member(member: 'Member') -> PriceLevel:
    return PriceLevel(member.price_level)

def get_discount_for_product(product: 'Product', price_level: PriceLevel) -> Discount:
    '''
    Check if this product gets a discount at the given price level, or if it stays at the normal price
    '''
    if price_level in map(PriceLevel, product.get_metadata(MakerspaceMetadataKeys.ALLOWED_PRICE_LEVELS, [])):
        return get_discount_fraction_off(price_level)
    else:
        return get_discount_fraction_off(PriceLevel.Normal)

def get_discount_fraction_off(price_level: PriceLevel) -> Discount:
    global DISCOUNT_FRACTIONS
    if DISCOUNT_FRACTIONS is None:
        DISCOUNT_FRACTIONS = {
            price_level: _query_discount_fraction_off(price_level) for price_level in PriceLevel
        }
    
    return DISCOUNT_FRACTIONS[price_level]

def _query_discount_fraction_off(price_level: PriceLevel) -> Discount:
    if price_level == PriceLevel.Normal:
        return Discount(None, Decimal(0))

    coupons: List[stripe.Coupon] = retry(lambda: stripe.Coupon.list())
    coupons = [coupon for coupon in coupons if coupon["metadata"].get(MakerspaceMetadataKeys.PRICE_LEVEL.value, None) == price_level.value]
    if len(coupons) == 0:
        raise Exception(f"Could not find stripe coupon for {MakerspaceMetadataKeys.PRICE_LEVEL.value}={price_level.value}")
    if len(coupons) > 1:
        raise Exception(f"Found multiple stripe coupons for {MakerspaceMetadataKeys.PRICE_LEVEL.value}={price_level.value}")
    
    coupon = coupons[0]
    if (coupon["amount_off"] or 0) > 0:
        raise Exception(f"Stripe coupon {coupon.stripe_id} has a fixed amount off. Only a percentage off is supported by MakerAdmin")

    percent_off = coupon["percent_off"]
    assert isinstance(percent_off, float) and percent_off >= 0 and percent_off <= 100
    return Discount(coupon, Decimal(percent_off) / 100)
