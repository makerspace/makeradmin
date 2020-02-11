from flask import g
from sqlalchemy.orm import contains_eager

from membership.models import Member, Span, Key
from multiaccess import service
from multiaccess.box_terminator import box_terminator_validate, box_terminator_nag, \
    box_terminator_boxes
from service.api_definition import GET, Arg, MEMBER_EDIT, POST, MEMBER_VIEW, symbol, MEMBERBOOTH
from service.db import db_session
from service.logging import logger


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


def memberbooth_response_object(member, key):
    return {
        'member_id': member.member_id,
        'key_id': key.key_id if key else None,
        'tagid': key.tagid if key else None,
        'description': key.description if key else None,
        'member': member_to_response_object(member)
    }


@service.route("/memberbooth/tag", method=GET, permission=MEMBERBOOTH)
def get_keys(tagid=Arg(int)):
    key = db_session.query(Key) \
        .filter(Key.tagid == tagid) \
        .join(Key.member) \
        .filter(
            Member.deleted_at.is_(None),
            Key.deleted_at.is_(None),
        ) \
        .first()

    if key is None:
        return None
    else:
        return memberbooth_response_object(key.member, key)


@service.route("/memberbooth/member", method=GET, permission=MEMBERBOOTH)
def memberbooth_member(member_number=Arg(int)):
    member = db_session.query(Member).filter(Member.member_number == member_number, Member.deleted_at.is_(None)).one()
    key = db_session.query(Key).filter(Key.member_id == member.member_id, Key.deleted_at.is_(None)).first()

    if member:
        return memberbooth_response_object(member, key)

    return None


@service.route("/box-terminator/boxes", method=GET, permission=MEMBER_EDIT)
def box_terminator_boxes_routes():
    """ Returns a list of all boxes scanned, ever. """
    return box_terminator_boxes()


@service.route("/box-terminator/nag", method=POST, permission=MEMBER_EDIT)
def box_terminator_nag_route(member_number=Arg(int), box_label_id=Arg(int), nag_type=Arg(symbol)):
    """ Send a nag email for this box. """
    return box_terminator_nag(member_number, box_label_id, nag_type)


@service.route("/box-terminator/validate-box", method=POST, permission=MEMBER_EDIT)
def box_terminator_validate_route(member_number=Arg(int), box_label_id=Arg(int)):
    """ Used when scanning boxes. """
    return box_terminator_validate(member_number, box_label_id, g.session_token)
