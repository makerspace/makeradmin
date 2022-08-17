from sqlalchemy.exc import NoResultFound

from membership.membership import get_membership_summary
from membership.models import Member
from multiaccessy.accessy import DummyAccessySession
from service.db import db_session


def maybe_send_accessy_labaccess_invite(member_id) -> str:
    """ If all preconditions are met, send an accessy invite (including auto add to labaccess gropup). Returns human
    readable message of what happened. """
    try:
        member = db_session.query(Member).get(member_id)
    except NoResultFound:
        return "member not found"

    if not member.phone:
        return "phone number not set for memeber"

    summary = get_membership_summary(member_id)
    if not summary.labaccess_active:
        return "no active labacess"

    accessy_session = DummyAccessySession.get()

    if accessy_session.is_in_org(member.phone):
        return "already in org, wait for next sync at midnight for access"

    accessy_session.invite_to_org_and_labacess_permissions(member.phone)
    
    return "invite sent"



