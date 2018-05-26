from flask import Flask
import service
from service import Entity
from dateutil import parser
from datetime import datetime, timedelta

key_entity = Entity(
    table="rfid",
    columns=["title", "description", "tagid", "status", "startdate", "enddate"],
    write_transforms={"startdate": lambda x: None if x is None else parser.parse(x), "enddate": lambda x: None if x is None else parser.parse(x)},
    # Expose the 'id' field as 'key_id'
    # Mostly for backwards compatibility with the old RFID module
    exposed_column_names={ "id": "key_id" }
)

with service.create(name="RFID", url="keys", port=80, version="1.0") as instance:
    app = Flask(__name__)
    gateway = instance.gateway

    key_entity.db = instance.db
    key_entity.add_routes(app, instance.full_path(""))

    @app.route(instance.full_path("update_times"), methods=["POST"])
    def update_keys():
        now = datetime.now().astimezone()
        transactions = gateway.get("webshop/transaction").json()["data"]

        for transaction in transactions:
            # Get the individual items in the transaction
            contents = gateway.get(f"webshop/transaction/{transaction['id']}/content").json()
            member_id = transaction["member_id"]
            for item in contents:
                if not item["completed"]:
                    # Check if the product has the appropriate action field for modifying membership
                    product = gateway.get(f"webshop/product/{item['product_id']}").json()
                    if product["action"].startswith("add_membership_days:"):
                        try:
                            days_to_add = int(product["action"].split(":")[1]) * item["count"]
                        except:
                            abort(400, f"Invalid action {product['action']} in product {product['name']}, parameter after colon should be an integer")

                        # Get all the member's keys
                        member_keys = gateway.get(f"related?param=/membership/member/{member_id}&matchUrl=/keys/(.*)&from=keys&page=1&sort_by=&sort_order=asc&per_page=10000").json()

                        if len(member_keys) == 0:
                            # To make sure that a member that purchases lab access before keys are handed out
                            # will still get their key activated when he/she gets a key.
                            eprint("Member has no keys, skipping the order")
                            continue

                        for key in member_keys:
                            # A bit inefficient, but we want to have nice objects that e.g have datetime fields instead of strings
                            key = key_entity.get(key["key_id"])
                            if now > key["enddate"]:
                                # Need to move forward the start date to start anew
                                key["startdate"] = key["enddate"] = now

                            key["enddate"] += timedelta(days=days_to_add)
                            r = gateway.put(f"keys/{key['key_id']}", key)
                            assert r.ok, r.text

                        item["completed"] = True
                        r = gateway.put("webshop/transaction_content/{item['id']}", item)
                        assert r.ok, r.text

    instance.serve_indefinitely(app)
