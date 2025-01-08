#!/usr/bin/env python3
from dataclasses import dataclass, field
from datetime import date, timedelta
from logging import getLogger
from typing import Dict, List, Optional

from membership.membership import get_members_and_membership, get_membership_summaries, get_membership_summary
from membership.models import Member, Span
from service.db import db_session
from sqlalchemy.orm import contains_eager

from multiaccessy.accessy import (
    ACCESSY_LABACCESS_GROUP,
    ACCESSY_SPECIAL_LABACCESS_GROUP,
    PHONE,
    AccessyMember,
    accessy_session,
)

logger = getLogger("makeradmin")


def get_wanted_access(today: date, member_id: Optional[int] = None) -> dict[PHONE, AccessyMember]:
    if member_id is not None:
        member = db_session.query(Member).get(member_id)
        if member is None:
            raise Exception("Member does not exist")
        members = [member]
        summaries = [get_membership_summary(member_id, at_date=today)]
    else:
        members, summaries = get_members_and_membership(at_date=today)

    return {
        member.phone: AccessyMember(
            phone=member.phone,
            name=f"{member.firstname} {member.lastname}",  # Never actually used
            groups={
                group
                for group, enabled in {
                    ACCESSY_SPECIAL_LABACCESS_GROUP: membership.special_labaccess_active,
                    ACCESSY_LABACCESS_GROUP: membership.labaccess_active,
                }.items()
                if enabled
            },
            member_id=member.member_id,
            member_number=member.member_number,
        )
        for member, membership in zip(members, summaries)
        if member.phone is not None and membership.effective_labaccess_active
    }


@dataclass
class GroupOp:
    member: AccessyMember
    group: str


@dataclass
class Diff:
    invites: List[AccessyMember] = field(default_factory=list)
    group_adds: List[GroupOp] = field(default_factory=list)
    group_removes: List[GroupOp] = field(default_factory=list)
    org_removes: List[AccessyMember] = field(default_factory=list)


def calculate_diff(actual_members: Dict[str, AccessyMember], wanted_members: Dict[str, AccessyMember]) -> Diff:
    diff = Diff()

    if ACCESSY_LABACCESS_GROUP is None or ACCESSY_SPECIAL_LABACCESS_GROUP is None:
        # We cannot perform diffing if
        logger.warning(
            "ACCESSY_LABACCESS_GROUP and/or ACCESSY_SPECIAL_LABACCESS_GROUP not configured, there will be no accessy diff"
        )
        return diff

    # Missing in Accessy, invite needed:
    for wanted in (wanted for phone, wanted in wanted_members.items() if phone not in actual_members):
        diff.invites.append(wanted)

    # Shouldn't have any access, remove from org needed:
    for actual in (actual for phone, actual in actual_members.items() if phone not in wanted_members):
        diff.org_removes.append(actual)

    # Already exists in accessy and should have access, but could be wrong groups:
    for phone, wanted in wanted_members.items():
        actual_m = actual_members.get(phone)

        if not actual_m:
            continue

        for group in wanted.groups - actual_m.groups:
            diff.group_adds.append(GroupOp(actual_m, group))

        for group in actual_m.groups - wanted.groups:
            diff.group_removes.append(GroupOp(actual_m, group))

    return diff


def sync(today: Optional[date] = None, member_id: Optional[int] = None) -> None:
    if accessy_session is None:
        logger.info(f"accessy sync skipped, accessy not configured.")
        return

    if not today:
        today = date.today()

    # If a specific member is given, sync only that member,
    # otherwise sync all members
    if member_id is not None:
        member = db_session.query(Member).get(member_id)
        if member is None:
            raise Exception("Member does not exist")
        if member.phone is None:
            return
        accessy_member = accessy_session.get_org_user_from_phone(member.phone)
        actual_members = [accessy_member] if accessy_member is not None else []
    else:
        actual_members = accessy_session.get_all_members()

    pending_invites = accessy_session.get_pending_invitations(after_date=today - timedelta(days=7))
    wanted_members = get_wanted_access(today, member_id=member_id)

    actual_members_by_phone = {}
    members_to_discard: List[AccessyMember] = []
    for m in actual_members:
        if m.phone:
            actual_members_by_phone[m.phone] = m
        else:
            # Members with no phone numbers are probably accounts that have gotten reset
            members_to_discard.append(m)

    diff = calculate_diff(actual_members_by_phone, wanted_members)

    for accessy_member in diff.invites:
        assert accessy_member.phone is not None
        if accessy_member.phone in pending_invites:
            logger.info(f"accessy sync skipping, invite already pending: {accessy_member}")
            continue
        logger.info(f"accessy sync inviting: {accessy_member}")
        accessy_session.invite_phone_to_org_and_groups([accessy_member.phone], accessy_member.groups)

    for op in diff.group_adds:
        logger.info(f"accessy sync adding to group: {op}")
        accessy_session.add_to_group(op.member, op.group)

    for op in diff.group_removes:
        logger.info(f"accessy sync removing from group: {op}")
        accessy_session.remove_from_group(op.member, op.group)

    for accessy_member in diff.org_removes:
        logger.info(f"accessy sync removing from org: {accessy_member}")
        accessy_session.remove_from_org(accessy_member)

    for accessy_member in members_to_discard:
        logger.info(f"accessy sync removing from org: {accessy_member}, because phone number is missing")
        accessy_session.remove_from_org(accessy_member)
