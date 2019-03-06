from flask import g

from membership.models import Member
from service.api_definition import WEBSHOP, WEBSHOP_EDIT, PUBLIC, GET, USER
from service.entity import Entity, OrmSingeRelation, ExpandField
from shop import service
from shop.models import Product, ProductCategory, Action, ProductAction, Transaction, TransactionContent, ProductImage
from shop.ordered_entity import OrderedEntity
from shop.product_image_entity import ProductImageEntity
from shop.shop import pending_actions

product_image_entity = ProductImageEntity(
    ProductImage,
    default_sort_column='display_order',
)


transaction_content_entity = Entity(
    TransactionContent,
    default_sort_column=None,
    expand_fields={'product': ExpandField(TransactionContent.product, [Product.name])},
)


transaction_entity = Entity(
    Transaction,
    expand_fields={'member': ExpandField(Transaction.member, [Member.firstname, Member.lastname, Member.member_number])},
)


service.entity_routes(
    path="/category",
    entity=OrderedEntity(ProductCategory),
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


service.entity_routes(
    path="/product",
    entity=OrderedEntity(Product),
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


service.related_entity_routes(
    path="/product/<int:related_entity_id>/images",
    entity=product_image_entity,
    relation=OrmSingeRelation('images', 'product_id'),
    permission_list=PUBLIC,
)


service.entity_routes(
    path="/action",
    entity=Entity(Action, default_sort_column=None),
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
)


service.entity_routes(
    path="/product_action",
    entity=Entity(ProductAction),
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
)


service.entity_routes(
    path="/transaction_content",
    entity=transaction_content_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
)


service.entity_routes(
    path="/transaction",
    entity=transaction_entity,
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
)

service.related_entity_routes(
    path="/transaction/<int:related_entity_id>/content",  # TODO BM -> /contents to be consistent
    entity=transaction_content_entity,
    relation=OrmSingeRelation('contents', 'transaction_id'),
    permission_list=WEBSHOP,
)


service.related_entity_routes(
    path="/member/<int:related_entity_id>/transactions",
    entity=transaction_entity,
    relation=OrmSingeRelation('member', 'member_id'),
    permission_list=WEBSHOP,
)


service.entity_routes(
    path="/product_image",
    entity=product_image_entity,
    permission_list=PUBLIC,
    permission_read=PUBLIC,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


@service.route("/member/current/pending_actions", method=GET, permission=USER)
def pending_actions_for_member():
    return pending_actions(g.user_id)
