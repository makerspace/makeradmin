from membership.models import Member
from service.entity import Entity, ExpandField
from shop.models import ProductImage, Transaction, TransactionContent, Product, TransactionAction, Action
from shop.ordered_entity import OrderedEntity
from shop.product_image_entity import ProductImageEntity

product_image_entity = ProductImageEntity(
    ProductImage,
    default_sort_column='display_order',
)


transaction_entity = Entity(
    Transaction,
    expand_fields={'member': ExpandField(Transaction.member, [Member.firstname, Member.lastname, Member.member_number])},
)


transaction_content_entity = Entity(
    TransactionContent,
    default_sort_column=None,
    expand_fields={'product': ExpandField(TransactionContent.product, [Product.name])},
)


transaction_action_entity = Entity(
    TransactionAction,
    default_sort_column=None,
    expand_fields={'action': ExpandField(TransactionAction.action, [Action.name])},
)


product_entity = OrderedEntity(Product)

