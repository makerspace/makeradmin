from membership.membership import get_membership_summary
from service.db import db_session
from service.error import NotFound
from membership.models import Member, Key
from .util import member_to_response_object


def memberbooth_response_object(member: Member, membership_data):
    response = member_to_response_object(member)
    del response["end_date"]
    response["membership_data"] = membership_data.as_json()
    return response


def tag_to_memberinfo(tagid: str):
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
    return memberbooth_response_object(key.member, membership_data)


def pin_login_to_memberinfo(member_id: int, pin_code: str):
    member = db_session.query(Member)\
        .filter(Member.member_id == member_id) \
        .filter(Member.pin_code == pin_code) \
        .filter(
            Member.pin_code.is_not(None),
            Member.deleted_at.is_(None),
        ) \
        .first()

    if member is None:
        raise NotFound(f"The member + pin code combination does not belong to any known user.")

    membership_data = get_membership_summary(member.member_id)
    return memberbooth_response_object(member, membership_data)


def member_number_to_memberinfo(member_number: int):
    member = db_session.query(Member).filter(Member.member_number == member_number, Member.deleted_at.is_(None)).first()

    if not member:
        return None

    membership_data = get_membership_summary(member.member_id)
    return memberbooth_response_object(member, membership_data)
