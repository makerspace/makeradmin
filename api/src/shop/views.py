from service.api_definition import WEBSHOP, WEBSHOP_EDIT, PUBLIC
from service.entity import Entity
from shop import service
from shop.models import Product, ProductCategory, Action, ProductAction, Transaction, TransactionContent, ProductImage
from shop.ordered_entity import OrderedEntity
from shop.product_image_entity import ProductImageEntity

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


service.entity_routes(
    path="/action",
    entity=Entity(Action),
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
    path="/transaction",
    entity=Entity(Transaction),
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
)


service.entity_routes(
    path="/transaction_content",
    entity=Entity(TransactionContent),
    permission_list=WEBSHOP,
    permission_read=WEBSHOP,
)


service.entity_routes(
    path="/product_image",
    entity=ProductImageEntity(ProductImage),
    permission_list=PUBLIC,
    permission_read=PUBLIC,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)





