from datetime import date, timedelta, datetime

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from membership.membership import get_labacess_end_date
from membership.models import Member, Box
from messages.views import message_entity
from service.db import db_session
from service.error import NotFound
from service.util import format_datetime, date_to_str, dt_to_str


def box_terminator_session_list(session_token=None):
    pass


def box_terminator_nag(member_number=None, box_label_id=None):
    try:
        box = db_session.query(Box).filter(Box.box_label_id == box_label_id,
                                           Member.member_number == member_number).one()
    except NoResultFound:
        raise NotFound()
    
    member = box.member

    message_entity.create({
        "recipients": [{"type": "member", "id": member.member_id}],
        "message_type": "email",
        "title": "Hämta din låda!",
        "description": (
            f"Hej,\n\nDin labacess gick ut {date_to_str(get_labacess_end_date(member))}"
            f", hämta lådan eller så går innehållet till makespace.\n\nHälsningar\nStockholm Makerpsace"
        )
    }, commit=False)

    box.last_nag_at = datetime.utcnow()
    

def box_terminator_validate(member_number=None, box_label_id=None, session_token=None):
    
    # Get member.
    
    try:
        member = db_session.query(Member).filter(Member.member_number == member_number).one()
    except NoResultFound:
        raise NotFound()

    # Get or create box.

    try:
        box = db_session.query(Box).filter(Box.box_label_id == box_label_id,
                                           Member.member_number == member_number).one()
    except NoResultFound:
        box = Box(member_id=member.member_id, box_label_id=box_label_id, session_token=session_token)
        
    box.last_check_at = datetime.utcnow()
    db_session.add(box)
    
    # Find out labaccess expiration date.
    
    expire_date = (get_labacess_end_date(member) or date(1997, 9, 26)) + timedelta(days=1)
    terminate_date = expire_date + timedelta(days=45)
    
    today = date.today()
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
        "expire_date": date_to_str(expire_date),
        "terminate_date": date_to_str(terminate_date),
        "status": status,
        "last_nag_at": dt_to_str(box.last_nag_at),
    }
