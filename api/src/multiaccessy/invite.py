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

from .sync import sync

logger = getLogger("makeradmin")


class AccessyInvitePreconditionFailed(AccessyError):
    pass


class LabaccessRequirements(Enum):
    OK = "OK"
    MEMBER_MISSING = "MEMBER_MISSING"
    NO_PHONE_NUMBER = "NO_PHONE_NUMBER"
    NO_LABACESS_AGREEMENT = "NO_LABACESS_AGREEMENT"


def check_labaccess_requirements(member_id: int) -> LabaccessRequirements:
    member = db_session.get(Member, member_id)
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

    sync(member_id=member_id)
