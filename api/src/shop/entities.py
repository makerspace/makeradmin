from membership.models import Member
from service.entity import ASC, DESC, Entity, ExpandField

from shop.models import (
    GiftCard,
    Product,
    ProductAction,
    ProductCategory,
    ProductGiftCardMapping,
    ProductImage,
    Transaction,
    TransactionAction,
    ProductCategory,
    ProductAction,
    TransactionAccount,
    TransactionCostCenter,
    ProductAccountsCostCenters,
    GiftCard,
    ProductGiftCardMapping,
    TransactionContent,
)
from shop.ordered_entity import OrderedEntity
from shop.product_image_entity import ProductImageEntity

category_entity = OrderedEntity(ProductCategory)


product_entity = OrderedEntity(
    Product,
    default_sort_column="name",
    default_sort_order=ASC,
    search_columns=("name", "description"),
    expand_fields={
        "product_accounting": ExpandField(
            Product.product_accounting,
            [ProductAccountsCostCenters.account_id, ProductAccountsCostCenters.cost_center_id],
        )
    },
)


product_action_entity = Entity(ProductAction)


product_image_entity = ProductImageEntity(
    ProductImage,
    search_columns=("name",),
)


transaction_entity = Entity(
    Transaction,
    expand_fields={
        "member": ExpandField(Transaction.member, [Member.firstname, Member.lastname, Member.member_number])
    },
    search_columns=("id", "created_at", "status", "member_id", "amount"),
)


transaction_content_entity = Entity(
    TransactionContent,
    default_sort_column=None,
    expand_fields={"product": ExpandField(TransactionContent.product, [Product.name])},
)


transaction_action_entity = Entity(
    TransactionAction,
    default_sort_column=None,
)


transaction_account_entity = OrderedEntity(
    TransactionAccount,
    default_sort_column="account",
    default_sort_order=ASC,
    search_columns=("account", "description"),
)

transaction_cost_center_entity = OrderedEntity(
    TransactionCostCenter,
    default_sort_column="cost_center",
    default_sort_order=ASC,
    search_columns=("cost_center", "description"),
)

product_accounting_entity = Entity(
    ProductAccountsCostCenters,
    default_sort_column="id",
    default_sort_order=ASC,
    search_columns=("cost_center_id", "account_id"),
)

gift_card_entity = Entity(
    GiftCard,
    default_sort_column="id",
    default_sort_order=DESC,
    search_columns=("id", "created_at", "status", "email"),
)

gift_card_content_entity = Entity(
    ProductGiftCardMapping,
    default_sort_column="id",
    default_sort_order=DESC,
    expand_fields={"product": ExpandField(ProductGiftCardMapping.product, [Product.name])},
)
