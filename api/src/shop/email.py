# TODO
# def send_new_member_email(member_id: int) -> None:
#     eprint("====== Getting member")
#     r = instance.gateway.get(f"membership/member/{member_id}")
#     assert r.ok
#     member = r.json()["data"]
#     eprint("====== Generating email body")
#     email_body = render_template("new_member_email.html", member=member, public_url=instance.gateway.get_public_url)
#     eprint("====== Sending new member email")
#
#     r = instance.gateway.post("messages/message", {
#         "recipients": [
#             {
#                 "type": "member",
#                 "id": member_id
#             },
#         ],
#         "message_type": "email",
#         "title": "Välkommen till Stockholm Makerspace",
#         "description": email_body
#     })
#
#     if not r.ok:
#         eprint("Failed to send new member email")
#         eprint(r.text)
#     eprint("====== Sent email body")
from flask import render_template

from membership.models import Member
from messages.views import message_entity
from service.config import get_public_url
from service.db import db_session
from service.util import date_to_str


def send_membership_updated_email(member_id, extended_days, end_date):
    member = db_session.query(Member).get(member_id)
    
    message_entity.create({
        "recipients": [{"type": "member", "id": member_id}],
        "message_type": "email",
        "title": "Ditt medlemsskap har utökats",
        "description": render_template(
            "updated_membership_time_email.html",
            public_url=get_public_url,
            member=member,
            extended_days=extended_days,
            end_date=date_to_str(end_date),
        )
    })


def send_key_updated_email(member_id, extended_days, end_date):
    member = db_session.query(Member).get(member_id)

    message_entity.create({
        "recipients": [{"type": "member", "id": member_id}],
        "message_type": "email",
        "title": "Din labaccess har utökats",
        "description": render_template(
            "updated_key_time_email.html",
            public_url=get_public_url,
            member=member,
            extended_days=extended_days,
            end_date=date_to_str(end_date),
        )
    })

