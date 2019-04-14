from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound

from membership.models import Member, Span, Key
from multiaccess import service
from multiaccess.box_terminator import box_terminator_validate
from service.api_definition import GET, KEYS_VIEW, SERVICE, MEMBER_VIEW, Arg, MEMBER_EDIT, POST
from service.db import db_session
from service.error import NotFound


def member_to_response_object(member):
    return {
        'member_id': member.member_id,
        'member_number': member.member_number,
        'firstname': member.firstname,
        'lastname': member.lastname,
        'end_date': max((span.enddate for span in member.spans)).isoformat() if len(member.spans) > 0 else None,
        'keys': [{'key_id': key.key_id, 'rfid_tag': key.tagid} for key in member.keys],
    }


@service.route("/memberdata", method=GET, permission=SERVICE)
def get_memberdata():
    query = db_session.query(Member).join(Member.spans).join(Member.keys)
    query = query.options(contains_eager(Member.spans), contains_eager(Member.keys))
    query = query.filter(
        Member.deleted_at.is_(None),
        Span.type.in_([Span.LABACCESS, Span.SPECIAL_LABACESS]),
        Span.deleted_at.is_(None),
        Key.deleted_at.is_(None),
    )

    return [member_to_response_object(m) for m in query]


def memberbooth_response_object(key):
    return {
        'member_id': key.member_id,
        'key_id': key.key_id,
        'tagid': key.tagid,
        'description': key.description,
        'member': member_to_response_object(key.member)
    }


@service.route("/memberbooth/tag/<int:tagid>", method=GET, permission=KEYS_VIEW)
def get_keys(tagid):
    query = db_session.query(Key)
    query = query.filter(Key.tagid == tagid)
    query = query.join(Key.member)
    query = query.filter(
        Member.deleted_at.is_(None),
        Key.deleted_at.is_(None),
    )

    taglookup = query.first()
    if taglookup is None:
        return None
    else:
        return memberbooth_response_object(taglookup)


@service.route("/box-terminator/session-list", method=GET, permission=MEMBER_EDIT)
def box_terminator_session_list_route():
    """ Returns a list of all boxes scanned in this session. """
    pass


@service.route("/box-terminator/nag", method=POST, permission=MEMBER_EDIT)
def box_terminator_nag_route(member_number=Arg(int), box_label_id=Arg(int)):
    """ Send a nag email for this box. """
    pass


@service.route("/box-terminator/validate-box", method=POST, permission=MEMBER_EDIT)
def box_terminator_validate_route(member_number=Arg(int), box_label_id=Arg(int)):
    """ Used when scanning boxes. """
    return box_terminator_validate(member_number, box_label_id)
