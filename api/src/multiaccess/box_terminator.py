from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from membership.models import Member, Span
from service.db import db_session
from service.error import NotFound


def box_terminator_session_list(session_token=None):
    pass


def box_terminator_nag(member_number=None, box_label_id=None):
    pass


def box_terminator_validate(member_number=None, box_label_id=None, session_token=None):
    try:
        member = db_session.query(Member).filter(Member.member_number == member_number).one()
    except NoResultFound:
        raise NotFound()

    query = db_session\
        .query(func.max(Span.enddate))\
        .filter(Span.member_id == member.member_id, Span.type.in_([Span.LABACCESS, Span.SPECIAL_LABACESS]))

    today = date.today()
    expire_date = (query.first()[0] or date(1997, 9, 26)) + timedelta(days=1)
    terminate_date = expire_date + timedelta(days=45)
    
    if today < expire_date:
        status = "active"
    elif today < terminate_date:
        status = "expired"
    else:
        status = "terminate"
        
    return {
        "box_label_id": box_label_id,
        "member_number": member.member_number,
        "name": f"{member.firstname} {member.lastname or ''}",
        "expire_date": expire_date.isoformat(),
        "terminate_date": terminate_date.isoformat(),
        "status": status,
        # TODO Add last nag date.
    }
