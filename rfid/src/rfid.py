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


def send_key_updated_email(member_id: int, extended_days: int, end_date: datetime) -> None:
    r = instance.gateway.get(f"membership/member/{member_id}")
    assert r.ok
    member = r.json()["data"]

    r = instance.gateway.post("messages", {
        "recipients": [
            {
                "type": "member",
                "id": member_id
            },
        ],
        "message_type": "email",
        "subject": "Din labaccess har utökats",
        "subject_en": "Your lab access has been extended",
        "body": render_template("updated_key_time_email.html", frontend_url=instance.gateway.get_frontend_url, member=member, extended_days=extended_days, end_date=end_date.strftime("%Y-%m-%d"))
    })

    if not r.ok:
        eprint("Failed to send key updated email")
        eprint(r.text)

@instance.route("update_times", methods=["POST"])
@route_helper
def update_keys() -> None:
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

        if action["name"] == "add_labaccess_days":
            days_to_add = int(pending["pending_action"]["value"])
            assert(days_to_add >= 0)
            r = gateway.post(f"membership/member/{member_id}/addMembershipSpan", { type: "labaccess", days: days_to_add })
            assert r.ok, r.text

            r = gateway.get(f"membership/member/{member_id}/membership")
            assert r.ok, r.text
            new_end_date = parser.parse(r.json()["data"]["labaccess_end"])

            r = gateway.put(f"webshop/transaction_action/{pending['pending_action']['id']}", { "status": "completed", "completed_at": str(now) })
            assert r.ok, r.text
            send_key_updated_email(member_id, days_to_add, new_end_date)


instance.serve_indefinitely()
