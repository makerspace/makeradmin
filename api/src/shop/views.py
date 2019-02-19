from service.api_definition import WEBSHOP, WEBSHOP_EDIT, PUBLIC
from service.entity import Entity
from shop import service
from shop.models import Product, ProductCategory, Action, ProductAction, Transaction, TransactionContent, ProductImage
from shop.ordered_entity import OrderedEntity


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
    entity=OrderedEntity(ProductImage),
    permission_list=PUBLIC,
    permission_read=PUBLIC,
    permission_create=WEBSHOP_EDIT,
    permission_update=WEBSHOP_EDIT,
    permission_delete=WEBSHOP_EDIT,
)


# The post route is handled separately for the image entity as it requires an upload
@instance.route("product_image", methods=["POST"], permission="webshop_edit")
@route_helper
def upload_image():
    data = request.get_json()
    if data is None:
        raise errors.MissingJson()

    product_id = int(assert_get(data, "product_id"))
    image = base64.b64decode(assert_get(data, "image"))
    image_name = assert_get(data, "image_name")
    if len(image) > 10_000_000:
        abort(400, "File too large")

    product = product_entity.get(product_id)
    if product is None:
        abort(404, "No such product")

    filename = product_images.save(FileStorage(io.BytesIO(image), filename=product["name"] + "_" + image_name))
    return product_image_entity.post({
        "product_id": product["id"],
        "path": filename,
        "caption": data["caption"] if "caption" in data else None
    })




