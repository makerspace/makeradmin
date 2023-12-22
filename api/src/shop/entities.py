from membership.models import Member
from service.entity import Entity, ExpandField, ASC, DESC
from shop.models import (
    ProductImage,
    Transaction,
    TransactionContent,
    Product,
    TransactionAction,
    ProductCategory,
    ProductAction,
    GiftCard,
    ProductGiftCardMapping,
)
from shop.ordered_entity import OrderedEntity
from shop.product_image_entity import ProductImageEntity

category_entity = OrderedEntity(ProductCategory)


product_entity = OrderedEntity(
    Product,
    default_sort_column="name",
    default_sort_order=ASC,
    search_columns=("name", "description"),
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
