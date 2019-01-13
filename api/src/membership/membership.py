from datetime import date, timedelta

from sqlalchemy import func

from membership.models import Span, LABACCESS, SPECIAL_LABACESS, MEMBERSHIP
from service.api_definition import NOT_UNIQUE
from service.db import db_session
from service.error import UnprocessableEntity


def get_membership_smmary(entity_id):
    today = date.today()
    
    has_labaccess = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type.in_([LABACCESS, SPECIAL_LABACESS]),
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )
    
    has_membership = bool(
        db_session
            .query(Span)
            .filter(Span.member_id == entity_id,
                    Span.type.in_([MEMBERSHIP]),
                    Span.startdate <= today,
                    Span.enddate >= today,
                    Span.deleted_at.is_(None))
            .count()
    )

    labaccess_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type.in_([LABACCESS, SPECIAL_LABACESS]),
        Span.deleted_at.is_(None)
    ).first()

    membership_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type.in_([MEMBERSHIP]),
        Span.deleted_at.is_(None)
    ).first()
    
    return dict(
        has_labaccess=has_labaccess,
        labaccess_end=labaccess_end.isoformat() if labaccess_end else None,
        has_membership=has_membership,
        membership_end=membership_end.isoformat() if membership_end else None,
    )


def add_membership_days(entity_id=None, type_=None, days=None, creation_reason=None, default_start_date=None):

    old_span = db_session.query(Span).filter_by(creation_reason=creation_reason).first()
    if old_span:
        if days == (old_span.enddate - old_span.startdate).days and type_ == old_span.type:
            # TODO Why is this something that we need to ignore?
            return get_membership_smmary(entity_id)
        raise UnprocessableEntity(f"Duplicate entry.", fields='creation_reason', what=NOT_UNIQUE)

    if not default_start_date:
        default_start_date = date.today()
        
    last_end, = db_session.query(func.max(Span.enddate)).filter(
        Span.member_id == entity_id,
        Span.type == type_,
        Span.deleted_at.is_(None)
    ).first()
    
    if not last_end or last_end < default_start_date:
        last_end = default_start_date

    end = last_end + timedelta(days=days)
    
    span = Span(member_id=entity_id, startdate=last_end, enddate=end, type=type_, creation_reason=creation_reason)
    db_session.add(span)
    db_session.commit()
    
    return get_membership_smmary(entity_id)
