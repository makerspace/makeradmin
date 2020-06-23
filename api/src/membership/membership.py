from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func

from membership.models import Span, Member
from service.api_definition import NOT_UNIQUE
from service.db import db_session
from service.error import UnprocessableEntity
from service.util import date_to_str


@dataclass(frozen=True)
class MembershipData:
    membership_end: date
    membership_active: bool
    labaccess_end: date
    labaccess_active: bool
    special_labaccess_end: date
    special_labaccess_active: bool
    
    # Should this member have access to the lab.
    effective_labaccess_end: date
    effective_labaccess_active: bool
    
    def as_json(self):
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


def max_or_none(*args):
    items = [i for i in args if i is not None]
    if items:
        return max(items)
    return None


def get_membership_summary(entity_id):
    today = date.today()
    
    labaccess_active = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type == Span.LABACCESS,
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )

    labaccess_end = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type == Span.LABACCESS,
        Span.deleted_at.is_(None)
    ).scalar()
    
    membership_active = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type == Span.MEMBERSHIP,
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )

    membership_end = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type == Span.MEMBERSHIP,
        Span.deleted_at.is_(None)
    ).scalar()
    
    special_labaccess_active = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type == Span.SPECIAL_LABACESS,
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )
    
    special_labaccess_end = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type == Span.SPECIAL_LABACESS,
        Span.deleted_at.is_(None)
    ).scalar()
    
    return MembershipData(
        labaccess_end=labaccess_end,
        labaccess_active=labaccess_active,
        special_labaccess_end=special_labaccess_end,
        special_labaccess_active=special_labaccess_active,
        membership_end=membership_end,
        membership_active=membership_active,
        effective_labaccess_end=max_or_none(labaccess_end, special_labaccess_end),
        effective_labaccess_active=labaccess_active or special_labaccess_active
    )


def get_members_and_membership():
    members = (
        db_session
        .query(Member)
        .filter(Member.deleted_at.is_(None))
    )

    memberships = [get_membership_summary(member.member_id) for member in members]
    return members, memberships


def add_membership_days(member_id=None, span_type=None, days=None, creation_reason=None, default_start_date=None):
    assert days >= 0

    old_span = db_session.query(Span).filter_by(creation_reason=creation_reason).first()
    if old_span:
        if days == (old_span.enddate - old_span.startdate).days and span_type == old_span.type:
            # Duplicate add days can happend because the code that handles the transactions is not yet done in a db
            # transaction, there are also an external script for handling puchases in ticktail that can create
            # dupllicates.
            return get_membership_summary(member_id)
        raise UnprocessableEntity(f"Duplicate entry.", fields='creation_reason', what=NOT_UNIQUE)

    if not default_start_date:
        default_start_date = date.today()
        
    last_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == member_id,
        Span.type == span_type,
        Span.deleted_at.is_(None)
    ).first()
    
    if not last_end or last_end < default_start_date:
        last_end = default_start_date

    end = last_end + timedelta(days=days)
    
    span = Span(member_id=member_id, startdate=last_end, enddate=end, type=span_type, creation_reason=creation_reason)
    db_session.add(span)
    db_session.flush()
    
    return get_membership_summary(member_id)
