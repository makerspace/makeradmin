from io import BytesIO

from PIL import Image, UnidentifiedImageError

from service.entity import Entity, logger
from service.error import BadRequest


class ProductImageEntity(Entity):
    
    def to_model(self, obj):
        model = super().to_model(obj)

        if "data" in model and "type" in model:
            try:
                image = Image.open(BytesIO(model["data"]))
            except UnidentifiedImageError:
                raise BadRequest("unsupported or invalid file format")
            image.thumbnail((500, 1_000_000), Image.ANTIALIAS)
            bytes = BytesIO()
            image.save(bytes, format="png", compress_level=8)
            model["data"] = bytes.getvalue()
            model["type"] = "image/png"
            if len(model["data"]) > 1_000_000:
                raise BadRequest("image too large")
            
        return model
