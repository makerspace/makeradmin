from io import BytesIO

from PIL import Image

from service.entity import Entity
from service.error import BadRequest


class ProductImageEntity(Entity):
    
    def to_model(self, obj):
        model = super().to_model(obj)

        if "data" in model and "type" in model:
            print("len1", len(model["data"]), model["name"])
            image = Image.open(BytesIO(model["data"]))
            print("size", image.width, image.height)
            image.thumbnail((500, 1_000_000), Image.ANTIALIAS)
            bytes = BytesIO()
            image.save(bytes, format="png", compress_level=8)
            print("size", image.width, image.height)
            model["data"] = bytes.getvalue()
            print("len2", len(model["data"]))
            model["type"] = 'image/png'

            if len(model["data"]) > 1_000_000:
                raise BadRequest("image too large")
            
        return model
    
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

