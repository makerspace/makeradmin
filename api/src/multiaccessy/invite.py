from sqlalchemy.exc import NoResultFound

from membership.membership import get_membership_summary
from membership.models import Member
from multiaccessy.accessy import DummyAccessySession, ACCESSY_LABACCESS_GROUP
from service.db import db_session


class AccessyError(Exception):
    pass


class AccessyInvitePrectionditionFailed(AccessyError):
    pass


def ensure_accessy_labaccess(member_id):
    """ If all preconditions are met, send an accessy invite (including auto add to labaccess gropup). Returns human
    readable message of what happened. """
    try:
        member = db_session.query(Member).get(member_id)
    except NoResultFound as e:
        raise AccessyInvitePrectionditionFailed("hittade inte medlem") from e

    if True or not member.phone:
        raise AccessyInvitePrectionditionFailed("inget telefonnummer")

    summary = get_membership_summary(member_id)
    if not summary.labaccess_active:
        raise AccessyInvitePrectionditionFailed("ingen aktiv labacess")

    try:
        accessy_session = DummyAccessySession.get()
        if accessy_session.is_in_org(member.phone):
            accessy_session.add_to_group(member.phone, ACCESSY_LABACCESS_GROUP)
        else:
            accessy_session.invite_phone_to_org_and_groups([member.phone], [ACCESSY_LABACCESS_GROUP])
    except Exception as e:
        raise AccessyError("failed to interact with accessy") from e
