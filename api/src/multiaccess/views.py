from flask import g
from sqlalchemy.orm import contains_eager

from membership.models import Member, Span, Key
from membership.membership import get_membership_summary
from multiaccess import service
from multiaccess import box_terminator
from service.api_definition import GET, Arg, MEMBER_EDIT, POST, MEMBER_VIEW, symbol, safe_text, iso_date, MEMBERBOOTH
from service.db import db_session


def member_to_response_object(member):
    return {
        'member_id': member.member_id,
        'member_number': member.member_number,
        'firstname': member.firstname,
        'lastname': member.lastname,
        'end_date': max((span.enddate for span in member.spans)).isoformat() if len(member.spans) > 0 else None,
        'keys': [{'key_id': key.key_id, 'rfid_tag': key.tagid} for key in member.keys],
    }


@service.route("/memberdata", method=GET, permission=MEMBER_VIEW)
def get_memberdata():
    """ Used by multiaccess sync program to get members. """
    query = db_session.query(Member).join(Member.spans).join(Member.keys)
    query = query.options(contains_eager(Member.spans), contains_eager(Member.keys))
    query = query.filter(
        Member.deleted_at.is_(None),
        Span.type.in_([Span.LABACCESS, Span.SPECIAL_LABACESS]),
        Span.deleted_at.is_(None),
        Key.deleted_at.is_(None),
    )

    return [member_to_response_object(m) for m in query]


def member_response_object(member, membership_data):
    response = member_to_response_object(member)
    del response["end_date"]
    response["membership_data"] = membership_data.as_json()
    return response


def get_member(member_number):
    member = db_session.query(Member).filter(Member.member_number == member_number, Member.deleted_at.is_(None)).first()

    if not member:
        return None

    membership_data = get_membership_summary(member.member_id)
    return member_response_object(member, membership_data)


@service.route("/memberbooth/tag", method=GET, permission=MEMBERBOOTH)
def memberbooth_tag(tagid=Arg(int)):
    key = db_session.query(Key)\
        .join(Key.member) \
        .filter(Key.tagid == tagid) \
        .filter(
            Member.deleted_at.is_(None),
            Key.deleted_at.is_(None),
        ) \
        .first()

    if key is None:
        return None

    membership_data = get_membership_summary(key.member_id)
    return member_response_object(key.member, membership_data)


@service.route("/memberbooth/member", method=GET, permission=MEMBERBOOTH)
def memberbooth_member(member_number=Arg(int)):
    return get_member(member_number)


@service.route("/box-terminator/stored_items", method=GET, permission=MEMBER_EDIT)
def box_terminator_stored_items(storage_type=Arg(symbol)):
    """ Returns a list of all items scanned of the storage type during the last seven days"""
    return box_terminator.box_terminator_stored_items()


@service.route("/box-terminator/nag", method=POST, permission=MEMBER_EDIT)
def box_terminator_nag(member_number=Arg(int), item_label_id=Arg(int), nag_type=Arg(symbol), description=Arg(safe_text, False)):
    """ Send a nag email for this storage type. """
    return box_terminator.box_terminator_nag(member_number, item_label_id, nag_type, description)


@service.route("/box-terminator/validate", method=POST, permission=MEMBER_EDIT)
def box_terminator_validate(member_number=Arg(int), item_label_id=Arg(int), storage_type=Arg(symbol), fixed_end_date=Arg(iso_date, False)):
    """ Used when scanning qr codes. """
    # Arg(isodate) converts from isoformat string to datetime
    return box_terminator.box_terminator_validate(member_number, item_label_id, storage_type, fixed_end_date)