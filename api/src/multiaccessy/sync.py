#!/usr/bin/env python3
import itertools
from dataclasses import dataclass, field
from datetime import date, timedelta
from logging import getLogger
from typing import Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar

from membership.membership import get_members_and_membership, get_membership_summaries, get_membership_summary
from membership.models import Group, GroupDoorAccess, Member, Span
from service.db import db_session
from sqlalchemy import select
from sqlalchemy.orm import contains_eager

from multiaccessy.accessy import (
    ACCESSY_LABACCESS_GROUP,
    ACCESSY_SPECIAL_LABACCESS_GROUP,
    PHONE,
    AccessyMember,
    ModificationsDisabledError,
    accessy_session,
)

logger = getLogger("makeradmin")

ACCESSY_GROUP_PREFIX = "makeradmin_group_"


def makeradmin_group_name_to_accessy_group_name(group_name: str) -> str:
    return f"{ACCESSY_GROUP_PREFIX}{group_name.lower().replace(' ', '_')}"


def get_wanted_access(
    today: date, group_ids_to_accessy_guids: Dict[int, str], member_id: Optional[int] = None
) -> dict[PHONE, AccessyMember]:
    if member_id is not None:
        member = db_session.query(Member).get(member_id)
        if member is None:
            raise Exception("Member does not exist")
        members = [member]
        summaries = [get_membership_summary(member_id, at_date=today)]
    else:
        members, summaries = get_members_and_membership(at_date=today)

    groups_by_member_res = db_session.execute(
        select(Member.member_id, Group.group_id)
        .join(Member.groups)
        .where(Member.deleted_at == None, Group.deleted_at == None)
    ).t
    member_ids_to_accessy_group_guids: Dict[int, Set[str]] = dict()
    for member_id, group_id in groups_by_member_res:
        if member_id not in member_ids_to_accessy_group_guids:
            member_ids_to_accessy_group_guids[member_id] = set()
        if group_id not in group_ids_to_accessy_guids:
            # This can happen if the accessy group could not be created, because accessy modifications are disabled
            continue
        group_guid = group_ids_to_accessy_guids[group_id]
        member_ids_to_accessy_group_guids[member_id].add(group_guid)

    for member, membership in zip(members, summaries):
        if member.member_id not in member_ids_to_accessy_group_guids:
            member_ids_to_accessy_group_guids[member.member_id] = set()
        if membership.special_labaccess_active:
            member_ids_to_accessy_group_guids[member.member_id].add(ACCESSY_SPECIAL_LABACCESS_GROUP)
        if membership.labaccess_active:
            member_ids_to_accessy_group_guids[member.member_id].add(ACCESSY_LABACCESS_GROUP)

    return {
        member.phone: AccessyMember(
            phone=member.phone,
            name=f"{member.firstname} {member.lastname}",  # Never actually used
            groups=member_ids_to_accessy_group_guids[member.member_id],
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


TItem = TypeVar("TItem")
TAttribute = TypeVar("TAttribute")


@dataclass
class Diff(Generic[TItem, TAttribute]):
    item_adds: List[TItem] = field(default_factory=list)
    item_removes: List[TItem] = field(default_factory=list)
    attribute_adds: List[Tuple[TItem, TAttribute]] = field(default_factory=list)
    attribute_removes: List[Tuple[TItem, TAttribute]] = field(default_factory=list)


# Diffs a set of items that have attributes
def calculate_diff(
    actual: Dict[TItem, Set[TAttribute]],
    wanted: Dict[TItem, Set[TAttribute]],
    skip_attributes_for_added_items: bool,
) -> Diff[TItem, TAttribute]:
    diff: Diff[TItem, TAttribute] = Diff()

    groups_wanted = wanted.keys()
    groups_actual = actual.keys()

    # Missing in Accessy, invite needed:
    for w in groups_wanted - groups_actual:
        diff.item_adds.append(w)

    # Shouldn't have any access, remove from org needed:
    for a in groups_actual - groups_wanted:
        diff.item_removes.append(a)

    # Already exists in accessy and should have access, but could be wrong groups:
    for group, wanted_elements in wanted.items():
        actual_elements = actual.get(group)

        if actual_elements is None:
            if skip_attributes_for_added_items:
                continue
            else:
                actual_elements = set()

        for element in wanted_elements - actual_elements:
            diff.attribute_adds.append((group, element))

        for element in actual_elements - wanted_elements:
            diff.attribute_removes.append((group, element))

    return diff


def sync_groups(today: date) -> Dict[int, str]:
    assert accessy_session is not None, "Accessy session must be initialized before syncing groups"

    if ACCESSY_LABACCESS_GROUP is None or ACCESSY_SPECIAL_LABACCESS_GROUP is None:
        logger.warning(
            "ACCESSY_LABACCESS_GROUP and/or ACCESSY_SPECIAL_LABACCESS_GROUP not configured, there will be no accessy diff"
        )

    existing_groups = [
        g for g in accessy_session.get_access_permission_groups() if g.name.startswith(ACCESSY_GROUP_PREFIX)
    ]

    existing_accesses = [accessy_session.get_access_permissions(g.id) for g in existing_groups]

    makeradmin_groups = db_session.scalars(select(Group).where(Group.deleted_at == None)).all()
    group_door_accesses = db_session.scalars(select(GroupDoorAccess).where(GroupDoorAccess.deleted_at == None)).all()

    wanted_groups = {
        makeradmin_group_name_to_accessy_group_name(group.name): {
            access.accessy_asset_publication_guid for access in group_door_accesses if access.group_id == group.group_id
        }
        for group in makeradmin_groups
    }
    # Remove groups that don't have any accesses, to keep things tidy
    wanted_groups = {name: accesses for name, accesses in wanted_groups.items() if len(accesses) > 0}

    diff = calculate_diff(
        {g.name: {a.assetPublication for a in accesses} for g, accesses in zip(existing_groups, existing_accesses)},
        wanted_groups,
        False,
    )

    for name in diff.item_adds:
        group = next(
            (g for g in makeradmin_groups if makeradmin_group_name_to_accessy_group_name(g.name) == name), None
        )
        assert group is not None
        logger.info(f"Creating Accessy group: {name}")
        try:
            new_g = accessy_session.create_access_permission_group(
                name, "Makeradmin group for " + group.name + ". Automatically created and managed by Makeradmin."
            )
            existing_groups.append(new_g)
        except ModificationsDisabledError:
            pass

    existing_groups_lookup = {g.name: g for g in existing_groups}

    for name in diff.item_removes:
        permission_group = existing_groups_lookup[name]
        logger.info(f"Removing Accessy group: {name}")
        accessy_session.delete_access_permission_group(permission_group.id)

    for name, asset_publication_id in diff.attribute_adds:
        if name not in existing_groups_lookup:
            logger.warning(f"Accessy group {name} not found, skipping access addition")
            # This can happen if accessy modifications have been disabled
            continue
        permission_group = existing_groups_lookup[name]
        logger.info(f"Adding access to Accessy group: {name} with access: {asset_publication_id}")
        accessy_session.create_access_permission_for_group(permission_group.id, asset_publication_id)

    for name, asset_publication_id in diff.attribute_removes:
        group_index = next((i for i, g in enumerate(existing_groups) if g.name == name), None)
        assert group_index is not None
        access = next((a for a in existing_accesses[group_index] if a.assetPublication == asset_publication_id), None)
        assert access is not None
        logger.info(f"Removing access from Accessy group: {name} with access: {asset_publication_id}")
        accessy_session.delete_access_permission(access.id)

    return {
        g.group_id: existing_groups_lookup[makeradmin_group_name_to_accessy_group_name(g.name)].id
        for g in makeradmin_groups
        if makeradmin_group_name_to_accessy_group_name(g.name) in existing_groups_lookup
    }


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

    group_ids_to_accessy_guids = sync_groups(today)
    pending_invites = accessy_session.get_pending_invitations(after_date=today - timedelta(days=7))
    wanted_members = get_wanted_access(
        today, member_id=member_id, group_ids_to_accessy_guids=group_ids_to_accessy_guids
    )

    actual_members_by_phone: Dict[str, AccessyMember] = {}
    members_to_discard: List[AccessyMember] = []
    for m in actual_members:
        if m.phone:
            actual_members_by_phone[m.phone] = m
        else:
            # Members with no phone numbers are probably accounts that have gotten reset
            members_to_discard.append(m)

    diff = calculate_diff(
        {phone: m.groups for (phone, m) in actual_members_by_phone.items()},
        {phone: m.groups for (phone, m) in wanted_members.items()},
        True,
    )

    for phone in diff.item_adds:
        accessy_member = wanted_members[phone]
        assert accessy_member.phone is not None, "Accessy member phone must not be None"
        if phone in pending_invites:
            logger.info(f"accessy sync skipping, invite already pending: {accessy_member}")
            continue
        logger.info(f"accessy sync inviting: {accessy_member}")
        accessy_session.invite_phone_to_org_and_groups([accessy_member.phone], accessy_member.groups)

    for phone, group in diff.attribute_adds:
        accessy_member = actual_members_by_phone[phone]
        logger.info(f"accessy sync adding to group: {(accessy_member.name, group)}")
        accessy_session.add_to_group(accessy_member, group)

    for phone, group in diff.attribute_removes:
        accessy_member = actual_members_by_phone[phone]
        logger.info(f"accessy sync removing from group: {(accessy_member.name, group)}")
        accessy_session.remove_from_group(accessy_member, group)

    for phone in diff.item_removes:
        accessy_member = actual_members_by_phone[phone]
        logger.info(f"accessy sync removing from org: {accessy_member}")
        accessy_session.remove_from_org(accessy_member)

    for accessy_member in members_to_discard:
        logger.info(f"accessy sync removing from org: {accessy_member}, because phone number is missing")
        accessy_session.remove_from_org(accessy_member)
