#!/usr/bin/env python3
from dataclasses import dataclass, field
from datetime import date, timedelta
from logging import getLogger

from sqlalchemy.orm import contains_eager

from membership.models import Member, Span
from multiaccessy.accessy import PHONE, AccessyMember, ACCESSY_LABACCESS_GROUP, ACCESSY_SPECIAL_LABACCESS_GROUP, \
    accessy_session
from service.db import db_session

logger = getLogger("makeradmin")


GROUPS = {
    Span.SPECIAL_LABACESS: ACCESSY_SPECIAL_LABACCESS_GROUP,
    Span.LABACCESS: ACCESSY_LABACCESS_GROUP,
}


def get_wanted_access(today) -> dict[PHONE, AccessyMember]:
    query = db_session.query(Member).join(Member.spans)
    query = query.options(contains_eager(Member.spans))
    query = query.filter(
        Member.deleted_at.is_(None),
        Member.phone.is_not(None),
        Member.labaccess_agreement_at.is_not(None),
        Span.type.in_([Span.LABACCESS, Span.SPECIAL_LABACESS]),
        Span.startdate <= today,
        Span.enddate >= today,
        Span.deleted_at.is_(None),
    )
    
    return {
        m.phone: AccessyMember(
            phone=m.phone,
            name=f"{m.firstname} {m.lastname}",
            groups={GROUPS[span.type] for span in m.spans},
            member_id=m.member_id,
            member_number=m.member_number,
        )
        for m in query
    }


@dataclass
class GroupOp:
    member: AccessyMember
    group: str


@dataclass
class Diff:
    invites: [AccessyMember] = field(default_factory=list)
    group_adds: [GroupOp] = field(default_factory=list)
    group_removes: [GroupOp] = field(default_factory=list)
    org_removes: [AccessyMember] = field(default_factory=list)


def calculate_diff(actual_members, wanted_members):
    diff = Diff()

    if ACCESSY_LABACCESS_GROUP is None or ACCESSY_SPECIAL_LABACCESS_GROUP is None:
        # We cannot perform diffing if
        logger.warning("ACCESSY_LABACCESS_GROUP and/or ACCESSY_SPECIAL_LABACCESS_GROUP not configured, there will be no accessy diff")
        return diff
    
    # Missing in Accessy, invite needed:
    for wanted in (wanted for phone, wanted in wanted_members.items() if phone not in actual_members):
        diff.invites.append(wanted)
        
    # Should have any access, remove from org needed:
    for actual in (actual for phone, actual in actual_members.items() if phone not in wanted_members):
        diff.org_removes.append(actual)

    # Already exists in accessy and should have access, but could be wrong groups:
    for phone, wanted in wanted_members.items():
        actual = actual_members.get(phone)
        
        if not actual:
            continue

        for group in wanted.groups - actual.groups:
            diff.group_adds.append(GroupOp(wanted, group))
    
        for group in actual.groups - wanted.groups:
            diff.group_removes.append(GroupOp(actual, group))
    
    return diff


def sync(today=None):
    if not today:
        today = date.today()
    
    actual_members = accessy_session.get_all_members()
    pending_invites = accessy_session.get_pending_invitations(after_date=today - timedelta(days=7))
    wanted_members = get_wanted_access(today)
    
    actual_members_by_phone = {}
    for m in actual_members:
        if m.phone:
            actual_members_by_phone[m.phone] = m
        else:
            logger.warning(f"accessy sync got member %s from accessy without phone number, skipping in calculation, will probably cause extra invite or delayed org remove", m)

    diff = calculate_diff(actual_members_by_phone, wanted_members)

    for member in diff.invites:
        if member.phone in pending_invites:
            logger.info(f"accessy sync skipping, invite already pending: {member}")
            continue
        logger.info(f"accessy sync inviting: {member}")
        accessy_session.invite_phone_to_org_and_groups([member.phone], member.groups)
    
    for op in diff.group_adds:
        logger.info(f"accessy sync adding to group: {op}")
        accessy_session.add_to_group(op.member.phone, op.group)
        
    for op in diff.group_removes:
        logger.info(f"accessy sync removing from group: {op}")
        accessy_session.remove_from_group(op.member.phone, op.group)
        
    for member in diff.org_removes:
        logger.info(f"accessy sync removing from org: {member}")
        accessy_session.remove_from_org(member.phone)
