from logging import getLogger

from membership.member_auth import verify_password
from membership.membership import get_membership_summary
from membership.models import Key, Member
from service.db import db_session
from service.error import NotFound

logger = getLogger("makeradmin")


def member_to_response_object(member: Member):
    return {
        "member_id": member.member_id,
        "member_number": member.member_number,
        "firstname": member.firstname,
        "lastname": member.lastname,
        "end_date": max((span.enddate for span in member.spans)).isoformat() if len(member.spans) > 0 else None,
        "keys": [{"key_id": key.key_id, "rfid_tag": key.tagid} for key in member.keys],
    }


def memberbooth_response_object(member: Member, membership_data):
    response = member_to_response_object(member)
    del response["end_date"]
    response["membership_data"] = membership_data.as_json()
    return response


def tag_to_memberinfo(tagid: str):
    key = (
        db_session.query(Key)
        .join(Key.member)
        .filter(Key.tagid == tagid)
        .filter(
            Member.deleted_at.is_(None),
            Key.deleted_at.is_(None),
        )
        .first()
    )

    if key is None:
        return None

    membership_data = get_membership_summary(key.member_id)
    return memberbooth_response_object(key.member, membership_data)


def pin_login_to_memberinfo(member_number: int, pin_code_or_password: str):
    member = (
        db_session.query(Member)
        .filter(Member.member_number == member_number)
        .filter(Member.deleted_at.is_(None))
        .first()
    )

    if member is None:
        logger.info("The member number did not match any known member")
        raise NotFound(f"The member + pin code combination does not belong to any known user.")

    if member.pin_code is None and member.password is None:
        logger.info(f"Member #{member.member_number} has not set a PIN code or password yet")
        raise NotFound(f"The member + pin code/password combination does not belong to any known user.")

    if verify_password(pin_code_or_password, member.password) or member.pin_code == pin_code_or_password:
        # Good, password matched
        pass
    else:
        logger.warning(f"Incorrect PIN code or password for member #{member.member_number}")
        raise NotFound(f"The member + pin code/password combination does not belong to any known user.")

    membership_data = get_membership_summary(member.member_id)
    return memberbooth_response_object(member, membership_data)


def member_number_to_memberinfo(member_number: int):
    member = db_session.query(Member).filter(Member.member_number == member_number, Member.deleted_at.is_(None)).first()

    if not member:
        return None

    membership_data = get_membership_summary(member.member_id)
    return memberbooth_response_object(member, membership_data)
