from sqlalchemy.exc import NoResultFound

from membership.membership import get_membership_summary
from membership.models import Member
from multiaccessy.accessy import DummyAccessySession
from service.db import db_session
from service.error import InternalServerError


def send_accessy_invite(member_id) -> str:
    try:
        member = db_session.query(Member).get(member_id)
    except NoResultFound:
        raise InternalServerError(log=f"No member with id {member_id} found, this is a bug.")

    if not member.phone:
        return "no phone"

    summary = get_membership_summary(member_id)
    if not summary.labaccess_active:
        return "no labacess"

    accessy_session = DummyAccessySession.get()
    accessy_session.invite_to_org_and_labacess_permissions(member.phone)
    
    return "invite sent"



