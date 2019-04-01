from sqlalchemy.orm import contains_eager

from membership.models import Member, Span, LABACCESS, SPECIAL_LABACESS, Key
from multiaccess import service
from service.api_definition import GET, KEYS_VIEW, SERVICE
from service.db import db_session


def member_to_response_object(member):
    return {
        'member_id': member.member_id,
        'member_number': member.member_number,
        'firstname': member.firstname,
        'lastname': member.lastname,
        'end_date': max((span.enddate for span in member.spans)).isoformat() if len(member.spans) > 0 else member.created_at,
        'keys': [{'key_id': key.key_id, 'rfid_tag': key.tagid} for key in member.keys],
    }


@service.route("/memberdata", method=GET, permission=SERVICE)
def get_memberdata():
    query = db_session.query(Member).join(Member.spans).join(Member.keys)
    query = query.options(contains_eager(Member.spans), contains_eager(Member.keys))
    query = query.filter(
        Member.deleted_at.is_(None),
        Span.type.in_([LABACCESS, SPECIAL_LABACESS]),
        Span.deleted_at.is_(None),
        Key.deleted_at.is_(None),
    )

    return [member_to_response_object(m) for m in query]

def key_to_response_object(key):
    return {
        'member_id': key.member_id,
        'key_id' : key.key_id,
        'tagid': key.tagid,
        'description': key.description,
        'member': member_to_response_object(key.member)
    }

@service.route("/keylookup/<int:tagid>", method=GET, permission=KEYS_VIEW)
def get_keys(tagid):
    query = db_session.query(Key)
    query = query.filter(Key.tagid == tagid)
    query = query.join(Key.member)
    query = query.filter(
        Member.deleted_at.is_(None),
        Key.deleted_at.is_(None),
    )

    return [key_to_response_object(m) for m in query]
