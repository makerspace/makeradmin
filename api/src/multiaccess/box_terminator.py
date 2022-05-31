from datetime import date, timedelta, datetime

from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound

from membership.models import Member, MemberStorage, Span, StorageNags
from messages.message import send_message
from messages.models import MessageTemplate
from service.db import db_session
from service.error import NotFound, BadRequest
from service.util import date_to_str, dt_to_str, str_to_date
from shop.transactions import pending_action_value_sum, ProductAction


JUDGMENT_DAY = date(1997, 9, 26)  # Used as default for missing lab access date
EXPIRATION_TIME = 45 #Number of days from expiration date to the termination date when the item is removed
FUTURE_LIMIT = 90 # Maximum number of days possible for fixed_end_date

# TODO
# Add nags for spray cans in box, chemicals in box, battery in box, random stuff/chaos around item

class Reason:
    LABACCESS_EXPIRED = 'labaccess_expired'
    DATE_EXPIRED = 'date_expired'
    BOTH_EXPIRED = 'both_expired'

class Status:
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

def get_dates(item):
    today = date.today()

    expire_lab_date = get_labacess_end_date(item)
    terminate_lab_date = get_expire_date_from_end_date(expire_lab_date)

    if item.fixed_end_date:
        fixed_end_date = item.fixed_end_date
        terminate_fixed_date = get_expire_date_from_end_date(fixed_end_date)

        to_termination_days = min( (terminate_fixed_date - today).days, (terminate_lab_date - today).days )
        days_after_expiration = max( (today - fixed_end_date).days, (today - expire_lab_date).days )
    else:
        fixed_end_date = None
        terminate_fixed_date = None

        to_termination_days = (terminate_lab_date - today).days
        days_after_expiration = (today - expire_lab_date).days

    pending_labaccess_days = pending_action_value_sum(item.member_id, ProductAction.ADD_LABACCESS_DAYS)

    return {
        "expire_lab_date": expire_lab_date,
        "terminate_lab_date": terminate_lab_date,
        "expire_fixed_date": fixed_end_date,
        "terminate_fixed_date": terminate_fixed_date,
        "to_termination_days": to_termination_days,
        "days_after_expiration": days_after_expiration,
        "pending_labaccess_days": pending_labaccess_days,
    }

def check_status(dates):
    today = date.today()

    if today <= dates["expire_lab_date"] or dates["pending_labaccess_days"] > 0:
        lab_status = Status.ACTIVE
    elif dates["expire_lab_date"] < today <= dates["terminate_lab_date"]:
        lab_status = Status.EXPIRED
    else:
        lab_status = Status.TERMINATE

    if dates["expire_fixed_date"] != None: #Not all items have a fixed end date
        if today <= dates["expire_fixed_date"]:
            fixed_date_status = Status.ACTIVE
        elif dates["expire_fixed_date"] < today <= dates["terminate_fixed_date"]:
            fixed_date_status = Status.EXPIRED
        else:
            fixed_date_status = Status.TERMINATE
    else:
        fixed_date_status = Status.ACTIVE

    status, reason = {
        (Status.ACTIVE, Status.ACTIVE): (Status.ACTIVE, None),
        (Status.EXPIRED, Status.ACTIVE): (Status.EXPIRED, Reason.LABACCESS_EXPIRED),
        (Status.ACTIVE, Status.EXPIRED): (Status.EXPIRED, Reason.DATE_EXPIRED),
        (Status.EXPIRED, Status.EXPIRED): (Status.EXPIRED, Reason.BOTH_EXPIRED),
        (Status.TERMINATE, Status.ACTIVE): (Status.TERMINATE, Reason.LABACCESS_EXPIRED),
        (Status.ACTIVE, Status.TERMINATE): (Status.TERMINATE, Reason.DATE_EXPIRED),
        (Status.TERMINATE, Status.EXPIRED): (Status.TERMINATE, Reason.BOTH_EXPIRED),
        (Status.EXPIRED, Status.TERMINATE): (Status.TERMINATE, Reason.BOTH_EXPIRED),
        (Status.TERMINATE, Status.TERMINATE): (Status.TERMINATE, Reason.BOTH_EXPIRED),
    }[(lab_status, fixed_date_status)]

    return status, reason

def get_storage_info(item):
    dates = get_dates(item)
    status, reason = check_status(dates)

    today = date.today()
    nags = []
    for nag in item.storage_nags:
        if (today - nag.nag_at).days < dates["days_after_expiration"]:
            nags.append(dt_to_str(nag))

    return {
        "item_label_id": item.item_label_id,
        "member_number": item.member.member_number,
        "storage_type": item.storage_type,
        "name": f"{item.member.firstname} {item.member.lastname or ''}",
        "days_after_expiration": dates["days_after_expiration"],
        "status": status,
        "reason": reason,
        "nags": nags,
        "last_check_at": dt_to_str(item.last_check_at),
    }

def box_terminator_stored_items(storage_type=None, num_days=None):
    if num_days is None:
        num_days = 7
    query = get_storage_query()
    limit = datetime.utcnow() - timedelta(days=num_days)
    filtered_query = filter(lambda item: item.last_check_at > limit and item.storage_type == storage_type, query)
    return [get_storage_info(s) for s in filtered_query.order_by(desc(MemberStorage.last_check_at))]

def box_terminator_nag(member_number=None, item_label_id=None, nag_type=None, description=None):
    try:
        item = db_session.query(MemberStorage).filter(MemberStorage.item_label_id == item_label_id,
                                           Member.member_number == member_number).one()
    except NoResultFound:
        raise NotFound("Bloop, prylen finns i Lettland")

    dates = get_dates(item)
    status, reason = check_status(dates)

    if item.storage_type == MemberStorage.BOX:
        try:
            template = {
                "nag-warning": MessageTemplate.BOX_WARNING,
                "nag-last-warning": MessageTemplate.BOX_FINAL_WARNING,
                "nag-terminated": MessageTemplate.BOX_TERMINATED,
            }[nag_type]
        except KeyError:
            raise BadRequest(f"Bad nag type {nag_type}")
    elif item.storage_type == MemberStorage.TEMP:
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
        raise BadRequest(f"Bad storage type {item.storage_type}")

    if item.storage_type == MemberStorage.TEMP:
        send_message(
            template, item.member,
            expiration_time=EXPIRATION_TIME,
            labaccess_end_date=date_to_str(dates["expire_lab_date"]),
            fixed_end_date=date_to_str(dates["fixed_end_date"]),
            to_termination_days=dates["to_termination_days"],
            days_after_expiration=dates["days_after_expiration"],
            description=description,
        )
    else:
        send_message(
            template, item.member,
            expiration_time=EXPIRATION_TIME,
            labaccess_end_date=date_to_str(dates["expire_lab_date"]),
            to_termination_days=dates["to_termination_days"],
            days_after_expiration=dates["days_after_expiration"],
        )

    nag = StorageNags(member_id=item.member_id, item_label_id=item_label_id, nag_at=datetime.utcnow(), nag_type=nag_type)
    db_session.add(nag)
    db_session.flush()

def box_terminator_validate(member_number=None, item_label_id=None, storage_type=None, fixed_end_date=None):
    today = date.today()
    if storage_type is None:
        raise BadRequest("No storage type")
    if storage_type != MemberStorage.BOX and storage_type != MemberStorage.TEMP:
        raise BadRequest("Unrecognized storage type")
    if fixed_end_date is None and storage_type == MemberStorage.TEMP:
        raise BadRequest("Temporary storage requires fixed expiration date.")
    #if (fixed_end_date - today).days> FUTURE_LIMIT:
    #    raise BadRequest("Fixed end date is further in the future than allowed maximum.")

    query = get_storage_query()
    query = query.filter(MemberStorage.item_label_id == item_label_id)
    try:
        item = query.one()
        found_item = True
        if storage_type != item.storage_type:
            raise BadRequest("Storage type argument does not match storage type in db.")
        if storage_type != MemberStorage.BOX:
            if fixed_end_date != item.fixed_end_date:
                raise BadRequest("Fixed end date does not match fixed end date in db.")
    except NoResultFound:
        found_item = False
        try:
            # Find the member since there was nothing in the db with the item_label_id
            member = db_session.query(Member).filter(Member.member_number == member_number).one()
        except NoResultFound:
            raise NotFound(f"Member not found {member_number}")
        item = MemberStorage(
            member_id=member.member_id,
            item_label_id=item_label_id,
            storage_type=storage_type,
            fixed_end_date = fixed_end_date,
        )

    item.last_check_at = datetime.utcnow()

    if not found_item:
        db_session.add(item)
    db_session.commit()

    return get_storage_info(item)