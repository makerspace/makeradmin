from decimal import Decimal
from service import Entity

# Note Decimal(str(x)) ensures it is a reasonable value that is saved.
# For example
# Decimal(0.2) = Decimal('0.200000000000000011102230246251565404236316680908203125')
# but
# Decimal("0.2") = Decimal('0.2')
product_entity = Entity(
    table="webshop_products",
    columns=["name", "category_id", "description", "unit", "price", "smallest_multiple"],
    write_transforms={"price": lambda x: Decimal(str(x))},
    read_transforms={"price": lambda x: str(x)},
)

category_entity = Entity(
    table="webshop_product_categories",
    columns=["name"]
)

transaction_content_entity = Entity(
    table="webshop_transaction_contents",
    columns=["transaction_id", "product_id", "count", "amount", "completed"],
    write_transforms={"amount": lambda x: Decimal(str(x))},
    read_transforms={"amount": lambda x: str(x)},
    allow_delete=False,
)

transaction_entity = Entity(
    table="webshop_transactions",
    columns=["member_id", "amount"],
    write_transforms={"amount": lambda x: Decimal(str(x))},
    read_transforms={"amount": lambda x: str(x)},
    allow_delete=False,
)
