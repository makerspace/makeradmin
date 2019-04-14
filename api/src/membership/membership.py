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
    has_labaccess: bool
    labaccess_end: date
    has_membership: bool
    membership_end: date
    # Differentiate the kind of membership the member has (either regular paid or special)
    has_labaccess_membership: bool
    labaccess_membership_end: date
    has_special_membership: bool
    special_membership_end: date
    
    def as_json(self):
        return dict(
            has_labaccess=self.has_labaccess,
            labaccess_end=date_to_str(self.labaccess_end),
            has_membership=self.has_membership,
            membership_end=date_to_str(self.membership_end),
            has_labaccess_membership=self.has_labaccess_membership,
            labaccess_membership_end=date_to_str(self.labaccess_membership_end),
            has_special_membership=self.has_special_membership,
            special_membership_end=date_to_str(self.special_membership_end)
        )


def get_membership_summary(entity_id):
    today = date.today()
    
    has_labaccess = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type.in_([Span.LABACCESS, Span.SPECIAL_LABACESS]),
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )
    
    has_labaccess_membership = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type.in_([Span.LABACCESS]),
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )
    
    has_special_membership = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type.in_([Span.SPECIAL_LABACESS]),
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )
    
    has_membership = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type.in_([Span.MEMBERSHIP]),
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )

    labaccess_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type.in_([Span.LABACCESS, Span.SPECIAL_LABACESS]),
        Span.deleted_at.is_(None)
    ).first()

    membership_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type.in_([Span.MEMBERSHIP]),
        Span.deleted_at.is_(None)
    ).first()

    labaccess_membership_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type.in_([Span.LABACCESS]),
        Span.deleted_at.is_(None)
    ).first()

    special_membership_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type.in_([Span.SPECIAL_LABACESS]),
        Span.deleted_at.is_(None)
    ).first()
    
    return MembershipData(
        has_labaccess=has_labaccess,
        labaccess_end=labaccess_end,
        has_membership=has_membership,
        membership_end=membership_end,
        has_labaccess_membership=has_labaccess_membership,
        labaccess_membership_end=labaccess_membership_end,
        has_special_membership=has_special_membership,
        special_membership_end=special_membership_end
    )


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
