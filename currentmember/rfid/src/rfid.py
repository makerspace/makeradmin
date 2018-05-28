from flask import Flask, abort
import service
from service import Entity, eprint, route_helper
from dateutil import parser
from datetime import datetime, timedelta

key_entity = Entity(
    table="rfid",
    columns=["title", "description", "tagid", "status", "startdate", "enddate"],
    write_transforms={"startdate": lambda x: None if x is None else parser.parse(x), "enddate": lambda x: None if x is None else parser.parse(x)},
    # Expose the 'id' field as 'key_id'
    # Mostly for backwards compatibility with the old RFID module
    exposed_column_names={"id": "key_id"}
)

instance = service.create(name="RFID", url="keys", port=80, version="1.0")
gateway = instance.gateway

key_entity.db = instance.db
key_entity.add_routes(instance, "")


@instance.route("update_times", methods=["POST"])
@route_helper
def update_keys():
    '''
    Completes all orders for purchasing lab access and updates existing keys with new dates.
    If a user has no key yet, then the order will remain as not completed.
    If a user has multiple keys, all of them are updated with new dates.
    '''
    now = datetime.now().astimezone()
    pending_actions = gateway.get("webshop/pending_actions").json()["data"]

    for pending in pending_actions:
        member_id = pending["member_id"]
        item = pending["item"]
        action = pending["action"]

        r = gateway.post("webshop/completed_actions", {
            "content_id": item["id"],
            "action_id": action["id"],
        })
        assert r.ok, r.text
        continue

        if action["name"] == "add_labaccess_days":
            days_to_add = int(item["action_value"]) * int(item["count"])
            assert(days_to_add >= 0)

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

            r = gateway.post("webshop/completed_actions", {
                "content_id": item["id"],
                "action_id": action["id"],
            })
            assert r.ok, r.text


instance.serve_indefinitely()
