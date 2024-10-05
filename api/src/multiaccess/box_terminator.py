from datetime import date, datetime, timedelta, timezone

from membership.models import Box, Member, Span
from messages.message import send_message
from messages.models import MessageTemplate
from service.db import db_session
from service.error import BadRequest, NotFound
from service.util import date_to_str, dt_to_str
from shop.transactions import ProductAction, pending_action_value_sum
from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound

JUDGMENT_DAY = date(1997, 9, 26)  # Used as default for missing lab access date.


def get_labacess_end_date(box):
    try:
        return max(
            s.enddate
            for s in box.member.spans
            if s.type in (Span.LABACCESS, Span.SPECIAL_LABACESS) and not s.deleted_at
        )
    except ValueError:
        return JUDGMENT_DAY


def get_box_query():
    query = db_session.query(Box).join(Member).outerjoin(Span)
    query = query.options(contains_eager(Box.member), contains_eager(Box.member).contains_eager(Member.spans))
    return query


def get_expire_date_from_labaccess_end_date(expire_date):
    if expire_date:
        return expire_date + timedelta(days=45)

    return JUDGMENT_DAY


def get_box_info(box):
    expire_date = get_labacess_end_date(box) + timedelta(days=1)
    terminate_date = get_expire_date_from_labaccess_end_date(expire_date)
    pending_labaccess_days = pending_action_value_sum(box.member_id, ProductAction.ADD_LABACCESS_DAYS)

    today = date.today()
    if today < expire_date or pending_labaccess_days > 0:
        status = "active"
    elif today < terminate_date:
        status = "expired"
    else:
        status = "terminate"

    return {
        "box_label_id": box.box_label_id,
        "member_number": box.member.member_number,
        "name": f"{box.member.firstname} {box.member.lastname or ''}",
        "expire_date": date_to_str(expire_date),
        "terminate_date": date_to_str(terminate_date),
        "status": status,
        "last_nag_at": dt_to_str(box.last_nag_at),
        "last_check_at": dt_to_str(box.last_check_at),
    }


def box_terminator_boxes():
    query = get_box_query()
    return [get_box_info(b) for b in query.order_by(desc(Box.last_check_at))]


def box_terminator_nag(member_number=None, box_label_id=None, nag_type=None):
    try:
        box = (
            db_session.query(Box).filter(Box.box_label_id == box_label_id, Member.member_number == member_number).one()
        )
    except NoResultFound:
        raise NotFound("Bloop, lådan finns i Lettland")

    try:
        template = {
            "nag-warning": MessageTemplate.BOX_WARNING,
            "nag-last-warning": MessageTemplate.BOX_FINAL_WARNING,
            "nag-terminated": MessageTemplate.BOX_TERMINATED,
        }[nag_type]

    except KeyError:
        raise BadRequest(f"Bad nag type {nag_type}")

    today = date.today()
    end_date = get_labacess_end_date(box)
    terminate_date = get_expire_date_from_labaccess_end_date(end_date)

    send_message(
        template,
        box.member,
        labaccess_end_date=date_to_str(end_date),
        to_termination_days=(terminate_date - today).days,
        days_after_expiration=(today - end_date).days,
    )

    box.last_nag_at = datetime.now(timezone.utc)


def box_terminator_validate(member_number=None, box_label_id=None, session_token=None):
    query = get_box_query()
    query = query.filter(Box.box_label_id == box_label_id)
    try:
        box = query.one()
    except NoResultFound:
        try:
            member = db_session.query(Member).filter(Member.member_number == member_number).one()
        except NoResultFound:
            raise NotFound()

        box = Box(member_id=member.member_id, box_label_id=box_label_id)

    box.last_check_at = datetime.now(timezone.utc)
    box.session_token = session_token
    db_session.add(box)
    db_session.flush()

    return get_box_info(box)
