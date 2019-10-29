from shop.ordered_entity import OrderedEntity


class ProductImageEntity(OrderedEntity):
    
    pass
    
    # Image upload to db:
    #
    # image = base64.b64decode(assert_get(data, "image"))
    # if len(image) > 10_000_000:
    #     abort(400, "File too large")
    #
    # filename = product_images.save(FileStorage(io.BytesIO(image), filename=product["name"] + "_" + image_name))
    # return product_image_entity.post({
    #     "product_id": product["id"],
    #     "path": filename,
    #     "caption": data["caption"] if "caption" in data else None
    # })

