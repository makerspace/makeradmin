from flask import Flask, abort, render_template
import service
from service import Entity, eprint, route_helper
from datetime import datetime, timedelta
from service import Column
from dateutil import parser

key_entity = Entity(
    table="rfid",
    columns=[
        # Expose the 'id' field as 'key_id'
        # Mostly for backwards compatibility with the old RFID module
        Column("id", write=None, exposed_name="key_id"),
        "title",
        "description",
        "tagid",
        "status",
        Column("startdate", dtype=datetime),
        Column("enddate", dtype=datetime),
    ],
)

instance = service.create(name="RFID", url="keys", port=80, version="1.0")
gateway = instance.gateway

key_entity.db = instance.db
key_entity.add_routes(instance, "", read_permission="keys_view", write_permission="keys_edit")

instance.serve_indefinitely()
