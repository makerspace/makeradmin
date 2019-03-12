from decimal import Decimal
from datetime import datetime
from backend_service import Entity, Column, DB, valid_database_identifier
from typing import List, Dict, Any, NamedTuple
from dataclasses import dataclass

# Note Decimal(str(x)) ensures it is a reasonable value that is saved.
# For example
# Decimal(0.2) = Decimal('0.200000000000000011102230246251565404236316680908203125')
# but
# Decimal("0.2") = Decimal('0.2')


# TODO Remove me

def membership_products(db: DB) -> List[Dict[str, Any]]:
    # Find all products which gives a member membership
    # Note: Assumes a product never contains multiple actions of the same type.
    # If this doesn't hold we will get duplicates of that product in the list.
    with db.cursor() as cur:
        cur.execute("""
            SELECT webshop_products.id,webshop_products.name,webshop_products.price FROM webshop_products
            INNER JOIN webshop_product_actions ON webshop_products.id=webshop_product_actions.product_id
            INNER JOIN webshop_actions ON webshop_actions.id=webshop_product_actions.action_id
            WHERE webshop_actions.name='add_membership_days' AND webshop_product_actions.deleted_at IS NULL
                  AND webshop_products.deleted_at IS NULL
        """)
        products = [{"id": v[0], "name": v[1], "price": float(v[2])} for v in cur.fetchall()]
        return products


