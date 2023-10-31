from datetime import date
from shop.models import Transaction
from membership.models import Member
from messages.message import send_message
from messages.models import MessageTemplate
from service.db import db_session
from service.util import date_to_str


def send_membership_updated_email(member_id: int, extended_days: int, end_date: date) -> None:
    member = db_session.query(Member).get(member_id)

    send_message(
        MessageTemplate.ADD_MEMBERSHIP_TIME, member, extended_days=extended_days, end_date=date_to_str(end_date)
    )


def send_labaccess_extended_email(member_id: int, extended_days: int, end_date: date) -> None:
    member = db_session.query(Member).get(member_id)

    send_message(
        MessageTemplate.ADD_LABACCESS_TIME, member, extended_days=extended_days, end_date=date_to_str(end_date)
    )


def send_receipt_email(transaction: Transaction) -> None:
    contents = transaction.contents
    products = [content.product for content in contents]

    send_message(
        MessageTemplate.RECEIPT,
        transaction.member,
        cart=list(zip(products, contents)),
        transaction=transaction,
        currency="kr",
    )


def send_new_member_email(member: Member) -> None:
    send_message(
        MessageTemplate.NEW_MEMBER,
        member,
    )
