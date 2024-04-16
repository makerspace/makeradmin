#!/usr/bin/env python3
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

import stripe
from dotenv import dotenv_values

env = dotenv_values()
stripe.api_key = env.get("STRIPE_PRIVATE_KEY")
currency = env.get("CURRENCY")


def to_stripe_currency(price: float) -> int:
    return int(price * 100)


parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "--yearly-price",
    metavar="PRICE",
    default=200,
    type=float,
    help="The price for base membership. Paid each year",
)
parser.add_argument(
    "--monthly-price",
    metavar="PRICE",
    default=300,
    type=float,
    help="The price for Makerspace access. Paid each month",
)
parser.add_argument(
    "--binding-period",
    metavar="MONTHS",
    default=2,
    type=int,
    help="The binding period in months.",
)
args = parser.parse_args()


yearly_price = args.yearly_price
monthly_price = args.monthly_price
binding_period_in_months = args.binding_period

exit(0)


base_membership = stripe.Product.create(
    name="Base membership",
    description="The base membership to the association",
    metadata={"subscription_type": "membership"},
)

price_yearly = stripe.Price.create(
    unit_amount=to_stripe_currency(yearly_price),
    currency=currency,
    recurring={"interval": "year", "interval_count": 1},
    product=base_membership["id"],
    metadata={"price_type": "recurring"},
)

makerspace_access = stripe.Product.create(
    name="Makerspace access",
    description="The base membership to the association",
    metadata={"subscription_type": "labaccess"},
)

price_subscription = stripe.Price.create(
    unit_amount=to_stripe_currency(monthly_price),
    currency=currency,
    recurring={"interval": "month", "interval_count": 1},
    product=makerspace_access["id"],
    metadata={"price_type": "recurring"},
)

price_binding_period = stripe.Price.create(
    unit_amount=to_stripe_currency(monthly_price * binding_period_in_months),
    currency=currency,
    recurring={"interval": "month", "interval_count": binding_period_in_months},
    product=makerspace_access["id"],
    metadata={"price_type": "binding_period"},
)

print(f"Base membership ID: {base_membership.id}")
print(f"- price ID: {price_yearly.id}")
print(f"Makerspace access ID: {makerspace_access.id}")
print(f"-   subscription price ID: {price_subscription.id}")
print(f"- binding period price ID: {price_binding_period.id}")
