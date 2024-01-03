from enum import Enum
from logging import getLogger

from membership.membership import get_membership_summary
from membership.models import Member
from service.db import db_session

from multiaccessy.accessy import (
    ACCESSY_CLIENT_SECRET,
    ACCESSY_LABACCESS_GROUP,
    ACCESSY_SPECIAL_LABACCESS_GROUP,
    AccessyError,
    accessy_session,
)

logger = getLogger("makeradmin")


class AccessyInvitePreconditionFailed(AccessyError):
    pass


class LabaccessRequirements(Enum):
    OK = "OK"
    MEMBER_MISSING = "MEMBER_MISSING"
    NO_PHONE_NUMBER = "NO_PHONE_NUMBER"
    NO_LABACESS_AGREEMENT = "NO_LABACESS_AGREEMENT"


def check_labaccess_requirements(member_id: int) -> LabaccessRequirements:
    member = db_session.query(Member).get(member_id)
    if member is None:
        return LabaccessRequirements.MEMBER_MISSING

    if not member.phone:
        return LabaccessRequirements.NO_PHONE_NUMBER

    if not member.labaccess_agreement_at:
        return LabaccessRequirements.NO_LABACESS_AGREEMENT

    return LabaccessRequirements.OK


def ensure_accessy_labaccess(member_id: int) -> None:
    """If all preconditions are met, send an accessy invite (including auto add to labaccess gropup). Returns human readable message of what happened."""

    if ACCESSY_CLIENT_SECRET is None:
        logger.warning("Missing accessy client secret: skipping updates")
        return

    state = check_labaccess_requirements(member_id)
    match state:
        case LabaccessRequirements.MEMBER_MISSING:
            raise AccessyInvitePreconditionFailed("hittade inte medlem")
        case LabaccessRequirements.NO_PHONE_NUMBER:
            raise AccessyInvitePreconditionFailed("inget telefonnummer")
        case LabaccessRequirements.NO_LABACESS_AGREEMENT:
            raise AccessyInvitePreconditionFailed("inget labbavtal")

    summary = get_membership_summary(member_id)
    if not summary.labaccess_active and not summary.special_labaccess_active:
        raise AccessyInvitePreconditionFailed("ingen aktiv labaccess")

    groups = []
    if summary.labaccess_active:
        groups.append(ACCESSY_LABACCESS_GROUP)
    if summary.special_labaccess_active:
        groups.append(ACCESSY_SPECIAL_LABACCESS_GROUP)

    member = db_session.query(Member).get(member_id)
    assert member is not None

    try:
        if accessy_session.is_in_org(member.phone):
            for group in groups:
                if not accessy_session.is_in_group(member.phone, group):
                    logger.info(f"accessy: user is already in org, addding to group: {member=} {group=}")
                    accessy_session.add_to_group(member.phone, group)
                else:
                    logger.info(f"accessy: user is already in group: {member=} {group=}")
        else:
            logger.info(f"accessy, sending invite: {member=} {groups=}")
            accessy_session.invite_phone_to_org_and_groups([member.phone], groups)
    except Exception as e:
        raise AccessyError("failed to interact with accessy") from e
