from decimal import Decimal
from datetime import datetime
from service import Entity, Column, DB
from typing import List, Dict, Any, NamedTuple
from dataclasses import dataclass

# Note Decimal(str(x)) ensures it is a reasonable value that is saved.
# For example
# Decimal(0.2) = Decimal('0.200000000000000011102230246251565404236316680908203125')
# but
# Decimal("0.2") = Decimal('0.2')


product_entity = Entity(
    table="webshop_products",
    columns=[
        "name",
        "category_id",
        "description",
        "unit",
        "filter",
        Column("price", dtype=Decimal),
        "smallest_multiple",
        Column("created_at", dtype=datetime, write=None),
        Column("updated_at", dtype=datetime, write=None)
    ],
)

category_entity = Entity(
    table="webshop_product_categories",
    columns=["name"]
)

transaction_content_entity = Entity(
    table="webshop_transaction_contents",
    columns=["transaction_id", "product_id", "count", Column("amount", dtype=Decimal)],
    allow_delete=False,
)

transaction_entity = Entity(
    table="webshop_transactions",
    columns=[
        "member_id",
        Column("status"),
        Column("created_at", dtype=datetime, write=None),
        Column("amount", dtype=Decimal)
    ],
    allow_delete=False,
)

action_entity = Entity(
    table="webshop_actions",
    columns=["name"],
    allow_delete=False,
)

product_action_entity = Entity(
    table="webshop_product_actions",
    columns=["product_id", "action_id", "value"],
)

webshop_stripe_pending = Entity(
    table="webshop_stripe_pending",
    columns=["transaction_id", "stripe_token"],
)

webshop_transaction_actions = Entity(
    table="webshop_transaction_actions",
    columns=["content_id", "action_id", "value", "status", Column("completed_at", dtype=datetime)],
)

webshop_pending_registrations = Entity(
    table="webshop_pending_registrations",
    columns=["transaction_id"],
)


def membership_products(db: DB) -> List[Dict[str,Any]]:
    # Find all products which gives a member membership
    # Note: Assumes a product never contains multiple actions of the same type.
    # If this doesn't hold we will get duplicates of that product in the list.
    with db.cursor() as cur:
        cur.execute("""
            SELECT webshop_products.id,webshop_products.name,webshop_products.price FROM webshop_products
            INNER JOIN webshop_product_actions ON webshop_products.id=webshop_product_actions.product_id
            INNER JOIN webshop_actions ON webshop_actions.id=webshop_product_actions.action_id
            WHERE webshop_actions.name='add_membership_days' AND webshop_product_actions.deleted_at IS NULL
        """)
        products = [{"id": v[0], "name": v[1], "price": v[2]} for v in cur.fetchall()]
        return products


@dataclass
class CartItem:
    name: str
    id: int
    count: int
    amount: Decimal
