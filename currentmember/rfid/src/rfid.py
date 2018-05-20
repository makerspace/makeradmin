from flask import Flask
import service
from service import Entity
from dateutil import parser

product_entity = Entity(
    table="rfid",
    columns=["title", "description", "tagid", "status", "startdate", "enddate"],
    write_transforms={"startdate": lambda x: None if x is None else parser.parse(x), "enddate": lambda x: None if x is None else parser.parse(x)},
    # Expose the 'id' field as 'key_id'
    # Mostly for backwards compatibility with the old RFID module
    exposed_column_names={ "id": "key_id" }
)

with service.create(name="RFID", url="keys", port=80, version="1.0") as instance:
    app = Flask(__name__)

    product_entity.db = instance.db
    product_entity.add_routes(app, instance.full_path(""))
    instance.serve_indefinitely(app)
