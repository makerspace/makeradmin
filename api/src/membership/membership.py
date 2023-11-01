from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func

from membership.models import Span, Member
from service.api_definition import NOT_UNIQUE
from service.db import db_session
from service.error import UnprocessableEntity, PreconditionFailed
from service.util import date_to_str
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar


@dataclass(frozen=True)
class MembershipData:
    membership_end: Optional[date]
    membership_active: bool
    labaccess_end: Optional[date]
    labaccess_active: bool
    special_labaccess_end: Optional[date]
    special_labaccess_active: bool

    # Should this member have access to the lab.
    effective_labaccess_end: Optional[date]
    effective_labaccess_active: bool

    def as_json(self) -> Dict[str, Optional[Any]]:
        return dict(
            membership_end=date_to_str(self.membership_end),
            membership_active=self.membership_active,
            labaccess_end=date_to_str(self.labaccess_end),
            labaccess_active=self.labaccess_active,
            special_labaccess_end=date_to_str(self.special_labaccess_end),
            special_labaccess_active=self.special_labaccess_active,
            effective_labaccess_end=date_to_str(self.effective_labaccess_end),
            effective_labaccess_active=self.effective_labaccess_active,
        )


T = TypeVar("T")


def max_or_none(*args: T) -> Optional[T]:
    items = [i for i in args if i is not None]
    if items:
        return max(items)
    return None


def get_membership_summary(member_id: int, at_date: Optional[date] = None) -> MembershipData:
    return get_membership_summaries([member_id], at_date)[0]


def get_membership_summaries(member_ids: List[int], at_date: Optional[date] = None) -> List[MembershipData]:
    """Returns a list of MembershipData for each member in member_ids."""

    # Speed up the database query for the common special case that member_ids is a list with exactly 1 element.
    # In other cases we will extract information about every member.
    # Since the method is only used with either 1 member or all members in the database this is reasonable.
    span_filter = Span.member_id == member_ids[0] if len(member_ids) == 1 else True

    if at_date is None:
        at_date = date.today()

    # Converts a list of rows of IDs to a set of them
    def setify(rows: List[Any]) -> Set[Any]:
        return set(r[0] for r in rows)

    # Converts a list of rows of IDs and values to a map from id to value
    def mapify(rows: List[Any]) -> Dict[Any, Any]:
        return {r[0]: r[1] for r in rows}

    labaccess_active = setify(
        db_session.query(Span.member_id)
        .filter(
            span_filter,
            Span.type == Span.LABACCESS,
            Span.startdate <= at_date,
            Span.enddate >= at_date,
            Span.deleted_at.is_(None),
        )
        .group_by(Span.member_id)
        .all()
    )

    labaccess_end = mapify(
        db_session.query(Span.member_id, func.max(Span.enddate))
        .filter(span_filter, Span.type == Span.LABACCESS, Span.deleted_at.is_(None))
        .group_by(Span.member_id)
        .all()
    )

    membership_active = setify(
        db_session.query(Span.member_id)
        .filter(
            span_filter,
            Span.type == Span.MEMBERSHIP,
            Span.startdate <= at_date,
            Span.enddate >= at_date,
            Span.deleted_at.is_(None),
        )
        .all()
    )

    membership_end = mapify(
        db_session.query(Span.member_id, func.max(Span.enddate))
        .filter(span_filter, Span.type == Span.MEMBERSHIP, Span.deleted_at.is_(None))
        .group_by(Span.member_id)
        .all()
    )

    special_labaccess_active = setify(
        db_session.query(Span.member_id)
        .filter(
            span_filter,
            Span.type == Span.SPECIAL_LABACESS,
            Span.startdate <= at_date,
            Span.enddate >= at_date,
            Span.deleted_at.is_(None),
        )
        .group_by(Span.member_id)
        .all()
    )

    special_labaccess_end = mapify(
        db_session.query(Span.member_id, func.max(Span.enddate))
        .filter(span_filter, Span.type == Span.SPECIAL_LABACESS, Span.deleted_at.is_(None))
        .group_by(Span.member_id)
        .all()
    )

    memberships: List[MembershipData] = []
    for id in member_ids:
        # Create the MembershipData structure
        # Note that the dict.get method returns None if the key doesn't exist in the map
        memberships.append(
            MembershipData(
                labaccess_end=labaccess_end.get(id),
                labaccess_active=id in labaccess_active,
                special_labaccess_end=special_labaccess_end.get(id),
                special_labaccess_active=id in special_labaccess_active,
                membership_end=membership_end.get(id),
                membership_active=id in membership_active,
                effective_labaccess_end=max_or_none(labaccess_end.get(id), special_labaccess_end.get(id)),
                effective_labaccess_active=(id in labaccess_active) or (id in special_labaccess_active),
            )
        )
    return memberships


def get_members_and_membership() -> Tuple[List[Member], List[MembershipData]]:
    members: List[Member] = db_session.query(Member).filter(Member.deleted_at.is_(None))
    memberships = get_membership_summaries([m.member_id for m in members])

    return members, memberships


def add_membership_days(
    member_id: int,
    span_type: str,
    days: int,
    creation_reason: Optional[str] = None,
    earliest_start_date: Optional[date] = None,
) -> MembershipData:
    assert days >= 0

    old_span = db_session.query(Span).filter_by(creation_reason=creation_reason).first()
    if old_span:
        if days == (old_span.enddate - old_span.startdate).days and span_type == old_span.type:
            # Duplicate add days can happend because the code that handles the transactions is not yet done in a db
            # transaction, there are also an external script for handling puchases in ticktail that can create
            # dupllicates.
            return get_membership_summary(member_id)
        raise UnprocessableEntity(f"Duplicate entry.", fields="creation_reason", what=NOT_UNIQUE)

    if not earliest_start_date:
        earliest_start_date = date.today()

    (last_end,) = (
        db_session.query(func.max(Span.enddate))
        .filter(Span.member_id == member_id, Span.type == span_type, Span.deleted_at.is_(None))
        .first()
    )

    if not last_end or last_end < earliest_start_date:
        last_end = earliest_start_date

    end = last_end + timedelta(days=days)

    span = Span(member_id=member_id, startdate=last_end, enddate=end, type=span_type, creation_reason=creation_reason)
    db_session.add(span)
    db_session.flush()

    return get_membership_summary(member_id)


def get_access_summary(member_id: int):
    from multiaccessy.accessy import accessy_session

    if accessy_session is None:
        return dict(in_org=False, pending_invite_count=0, access_permission_group_names=[])
    member: Member = db_session.query(Member).filter(Member.member_id == member_id).one()

    msisdn = member.phone
    pending_invite_count = sum(1 for no in accessy_session.get_pending_invitations() if no == msisdn)
    groups = accessy_session.get_user_groups(msisdn)

    return dict(
        in_org=accessy_session.is_in_org(msisdn),
        pending_invite_count=pending_invite_count,
        access_permission_group_names=groups,
    )
