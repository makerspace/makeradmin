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
    }, commit=False)


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
    }, commit=False)


def send_receipt_email(transaction):
    contents = transaction.contents
    products = [content.product for content in contents]

    message_entity.create({
        "recipients": [{"type": "member", "id": transaction.member_id}],
        "message_type": "email",
        "title": "Kvitto - Stockholm Makerspace",
        "description": render_template(
            "receipt_email.html",
            cart=zip(products, contents),
            transaction=transaction,
            currency="kr",
            member=transaction.member,
            public_url=get_public_url,
        )
    }, commit=False)


def send_new_member_email(member):
    message_entity.create({
        "recipients": [{"type": "member", "id": member.member_id}],
        "message_type": "email",
        "title": "Välkommen till Stockholm Makerspace",
        "description": render_template(
            "new_member_email.html",
            member=member,
            public_url=get_public_url,
        )
    }, commit=False)
