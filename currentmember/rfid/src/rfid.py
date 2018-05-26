from flask import Flask
import service
from service import Entity, eprint
from dateutil import parser
from datetime import datetime, timedelta

lab_action = "add_lab_access_days"

key_entity = Entity(
    table="rfid",
    columns=["title", "description", "tagid", "status", "startdate", "enddate"],
    write_transforms={"startdate": lambda x: None if x is None else parser.parse(x), "enddate": lambda x: None if x is None else parser.parse(x)},
    # Expose the 'id' field as 'key_id'
    # Mostly for backwards compatibility with the old RFID module
    exposed_column_names={"id": "key_id"}
)

instance = service.create(name="RFID", url="keys", port=80, version="1.0")
app = Flask(__name__)
gateway = instance.gateway

key_entity.db = instance.db
key_entity.add_routes(app, instance.full_path(""))


@app.route(instance.full_path("update_times"), methods=["POST"])
def update_keys():
    '''
    Completes all orders for purchasing lab access and updates existing keys with new dates.
    If a user has no key yet, then the order will remain as not completed.
    If a user has multiple keys, all of them are updated with new dates.
    '''
    now = datetime.now().astimezone()
    transactions = gateway.get("webshop/transaction").json()["data"]

    for transaction in transactions:
        member_id = transaction["member_id"]
        # Get the individual items in the transaction
        contents = gateway.get(f"webshop/transaction/{transaction['id']}/content").json()

        for item in contents:
            if not item["completed"]:
                # Get the product data from the transaction
                product = gateway.get(f"webshop/product/{item['product_id']}").json()["data"]
                # Check if the product has the appropriate action field for modifying membership
                if product["action"].startswith(lab_action + ":"):
                    days_to_add_str = product["action"].split(":")[1]
                    try:
                        days_to_add = int(days_to_add_str) * item["count"]
                    except ValueError:
                        abort(400, f"Invalid action {product['action']} in product {product['name']}, parameter after colon should be an integer")

                    # Get all the member's keys
                    # These will be on the form /keys/<int>
                    member_key_urls = gateway.get(f"related?param=/membership/member/{member_id}&matchUrl=/keys/(.*)&page=1&sort_by=&sort_order=asc&per_page=10000").json()["data"]
                    member_keys = [key_entity.get(int(url.split("/")[-1])) for url in member_key_urls]

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
                        key_entity.put(key["key_id"], key)

                    item["completed"] = True
                    r = gateway.put(f"webshop/transaction_content/{item['id']}", item)
                    assert r.ok, r.text


instance.serve_indefinitely(app)
