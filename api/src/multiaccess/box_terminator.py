from datetime import date, timedelta, datetime

from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound

from membership.models import Member, MemberStorage, Span
from messages.message import send_message
from messages.models import MessageTemplate
from service.db import db_session
from service.error import NotFound, BadRequest
from service.util import date_to_str, dt_to_str
from shop.transactions import pending_action_value_sum, ProductAction


JUDGMENT_DAY = date(1997, 9, 26)  # Used as default for missing lab access date
RESISTANCE_VICTORY_DAY = date(2029, 1, 1) # Used as default for missing fixed end date for storage
EXPIRATION_TIME = 45 #Number of days from expiration date to the termination date when the item is removed

class Reason(enum.Enum):
    LABACCESS_EXPIRED = 'labaccess_expired'
    DATE_EXPIRED = 'date_expired'
    BOTH_EXPIRED = 'both_expired'

class Status(enum.Enum):
    ACTIVE = 'active'
    EXPIRED = 'expired'
    TERMINATE = 'terminate'

def get_labacess_end_date(item):
    try:
        return max(s.enddate for s in item.member.spans
                   if s.type in (Span.LABACCESS, Span.SPECIAL_LABACESS) and not s.deleted_at)
    except ValueError:
        return JUDGMENT_DAY

def get_storage_query():
    query = db_session.query(MemberStorage).join(Member).outerjoin(Span)
    query = query.options(contains_eager(MemberStorage.member), contains_eager(MemberStorage.member).contains_eager(Member.spans))
    return query

def get_expire_date_from_end_date(expire_date):
    if expire_date:
        return expire_date + timedelta(days=EXPIRATION_TIME)

def check_status(item):
    today = date.today()

    expire_lab_date = get_labacess_end_date(item) + timedelta(days=1)
    terminate_lab_date = get_expire_date_from_end_date(expire_date)
    expire_fixed_date = item.fixed_end_date + timedelta(days=1)
    terminate_fixed_date = get_expire_date_from_end_date(item.fixed_end_date)
    pending_labaccess_days = pending_action_value_sum(item.member_id, ProductAction.ADD_LABACCESS_DAYS)

    if today <= expire_lab_date or pending_labaccess_days > 0:
        lab_status = Status.ACTIVE
    elif expire_lab_date < today <= terminate_lab_date:
        lab_status = Status.EXPIRED
    else:
        lab_status = Status.TERMINATE

    if today <= expire_fixed_date:
        fixed_date_status = Status.ACTIVE
    elif expire_fixed_date < today <= terminate_fixed_date:
        fixed_date_status = Status.EXPIRED
    else:
        fixed_date_status = Status.TERMINATE

    status, reason = {
        Status.ACTIVE, Status.ACTIVE: Status.ACTIVE, None,
        Status.EXPIRED, Status.ACTIVE: Status.EXPIRED, Reason.LABACCESS_EXPIRED,
        Status.ACTIVE, Status.EXPIRED: Status.EXPIRED, Reason.DATE_EXPIRED,
        Status.EXPIRED, Status.EXPIRED: Status.EXPIRED, Reason.BOTH_EXPIRED,
        Status.TERMINATE, Status.ACTIVE: Status.TERMINATE, Reason.LABACCESS_EXPIRED,
        Status.ACTIVE, Status.TERMINATE: Status.TERMINATE, Reason.DATE_EXPIRED,
        Status.TERMINATE, Status.EXPIRED: Status.TERMINATE, Reason.BOTH_EXPIRED,
        Status.EXPIRED, Status.TERMINATE: Status.TERMINATE, Reason.BOTH_EXPIRED,
        Status.TERMINATE, Status.TERMINATE: Status.TERMINATE, Reason.BOTH_EXPIRED,
    }[lab_status, fixed_date_status]

    return status, reason

def get_storage_info(item):
    status, reason = check_status(item)

    nags = []
    for d in item.storage_nags:
        nags.append(dt_to_str(d))

    return {
        "label_id": item.label_id,
        "member_number": item.member.member_number,
        "name": f"{box.member.firstname} {box.member.lastname or ''}",
        "expire_date": date_to_str(expire_date),
        "terminate_date": date_to_str(terminate_date),
        "fixed_end_date": date_to_str(fixed_end_date),
        "status": status,
        "nags": nags,
        "last_check_at": dt_to_str(item.last_check_at),
    }

def box_terminator_stored_items(storage_type=None):
    query = get_storage_query()
    limit = datetime.utcnow() - timedelta(days=7)
    filtered_query = filter(lambda item: item.last_check_at > limit and item.storage_type == storage_type, query)
    return [get_storage_info(s) for s in filtered_query.order_by(desc(MemberStorage.last_check_at))]

def box_terminator_nag(member_number=None, label_id=None, storage_type=None, nag_type=None, description=None):
    try:
        item = db_session.query(MemberStorage).filter(MemberStorage.label_id == label_id,
                                           Member.member_number == member_number).one()
    except NoResultFound:
        raise NotFound("Bloop, prylen finns i Lettland")

    status, reason = check_status(item)

    if storage_type == "box":
        try:
            template = {
                "nag-warning": MessageTemplate.BOX_WARNING,
                "nag-last-warning": MessageTemplate.BOX_FINAL_WARNING,
                "nag-terminated": MessageTemplate.BOX_TERMINATED,
            }[nag_type]
        except KeyError:
            raise BadRequest(f"Bad nag type {nag_type}")
    elif storage_type == "temp":
        try:
        template = {
            ("nag-warning", Reason.LABACCESS_EXPIRED): MessageTemplate.TEMP_STORAGE_WARNING_LAB,
            ("nag-last-warning", Reason.LABACCESS_EXPIRED): MessageTemplate.TEMP_STORAGE_WARNING_LAB,
            ("nag-terminated", Reason.LABACCESS_EXPIRED): MessageTemplate.TEMP_STORAGE_TERMINATED_LAB,
            ("nag-warning", Reason.DATE_EXPIRED): MessageTemplate.TEMP_STORAGE_WARNING_DATE,
            ("nag-last-warning", Reason.DATE_EXPIRED): MessageTemplate.TEMP_STORAGE_WARNING_DATE,
            ("nag-terminated", Reason.DATE_EXPIRED): MessageTemplate.TEMP_STORAGE_TERMINATED_DATE,
            ("nag-warning", Reason.BOTH_EXPIRED): MessageTemplate.TEMP_STORAGE_WARNING_BOTH,
            ("nag-last-warning", Reason.BOTH_EXPIRED): MessageTemplate.TEMP_STORAGE_WARNING_BOTH,
            ("nag-terminated", Reason.BOTH_EXPIRED): MessageTemplate.TEMP_STORAGE_TERMINATED_BOTH,
        }[(nag_type, reason)]
        except KeyError:
            raise BadRequest(f"Bad nag type {nag_type}")
    else:
        raise BadRequest(f"Bad storage type {storage_type}")

    today = date.today()

    lab_end_date = get_labacess_end_date(item)
    fixed_end_date = item.fixed_end_date
    terminate_lab_date = get_expire_date_from_end_date(lab_end_date)
    terminate_fixed_date = get_expire_date_from_end_date(fixed_end_date)
    to_termination_days = min(terminate_fixed_date - today, terminate_lab_date - today).days
    days_after_expiration = max(today - fixed_end_date, today - lab_end_date).days

    send_message(
        template, item.member,
        expiration_time = EXPIRATION_TIME,
        labaccess_end_date = date_to_str(lab_end_date),
        fixed_end_date = date_to_str(fixed_end_date),
        to_termination_days = to_termination_days,
        days_after_expiration = days_after_expiration,
        description = description,
    )

    nag = StorageNags(member_id=member.member_id, label_id=label_id, nag_at=datetime.utcnow(), nag_type=nag_type)
    db_session.add(nag)
    db_session.flush()

def box_terminator_validate(member_number=None, label_id=None, storage_type=None, fixed_end_date=RESISTANCE_VICTORY_DAY):
    if storage_type == None:
        raise BadRequest("No storage type")

    query = get_storage_query()
    query = query.filter(MemberStorage.label_id == label_id)
    try:
        storage = query.one()
    except NoResultFound:
        try:
            #Find the member since there was nothing in the db with the label_id
            member = db_session.query(Member).filter(Member.member_number == member_number).one()
        except NoResultFound:
            raise NotFound(f"Member not found {member_number}")
        item = MemberStorage(member_id=member.member_id, label_id=label_id, storage_type=storage_type)

    item.last_check_at = datetime.utcnow()
    item.fixed_end_date = fixed_end_date
    db_session.add(item)
    db_session.flush()

    return get_storage_info(item)
