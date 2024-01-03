from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from box_terminator.models import StorageItem, StorageMessage, StorageMessageType, StorageType
from membership.models import Member, Span
from messages.message import send_message
from messages.models import MessageTemplate
from service.db import db_session
from service.error import BadRequest, NotFound
from service.util import date_to_str, dt_to_str, str_to_date
from shop.transactions import ProductAction, pending_action_value_sum
from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound

JUDGMENT_DAY = datetime(1997, 9, 26)  # Used as default for missing lab access date
EXPIRATION_TIME = 45  # Number of days from expiration date to the termination date when the item is removed
FUTURE_LIMIT = 90  # Maximum number of days possible for fixed_end_date


class Reason:
    ACCESS_EXPIRED = "access_expired"
    DATE_EXPIRED = "date_expired"


class Status:
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATE = "terminate"


@dataclass
class BoxTerminatorButton:  # TODO
    text: str
    action: str
    url: str


@dataclass
class StorageInfo:
    name: str
    days_after_expiration: int
    status: Status
    reason: Reason
    messages: List[StorageMessage]
    buttons: List[BoxTerminatorButton]


def get_expire_date_from_end_date(expire_date: datetime) -> datetime:
    return expire_date + timedelta(days=EXPIRATION_TIME)


def get_labacess_end_date(item: StorageItem) -> datetime:
    try:
        return max(
            s.enddate
            for s in item.member.spans
            if s.type in (Span.LABACCESS, Span.SPECIAL_LABACESS) and not s.deleted_at
        )
    except ValueError:
        return JUDGMENT_DAY


def get_dates(item: StorageItem) -> Dict[str, datetime]:
    today = date.today()

    expire_lab_date = get_labacess_end_date(item)
    terminate_lab_date = get_expire_date_from_end_date(expire_lab_date)

    if item.storage_type.has_fixed_end_date:
        fixed_end_date = item.fixed_end_date
        terminate_fixed_date = get_expire_date_from_end_date(fixed_end_date)

        to_termination_days = min((terminate_fixed_date - today).days, (terminate_lab_date - today).days)
        days_after_expiration = max((today - fixed_end_date).days, (today - expire_lab_date).days)
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


def check_status(dates: Dict[str, datetime]) -> Tuple[Status, List[Reason]]:
    today = date.today()

    if today <= dates["expire_lab_date"] or dates["pending_labaccess_days"] > 0:
        lab_status = Status.ACTIVE
    elif dates["expire_lab_date"] < today <= dates["terminate_lab_date"]:
        lab_status = Status.EXPIRED
    else:
        lab_status = Status.TERMINATE

    if dates["expire_fixed_date"] != None:  # Not all items have a fixed end date
        if today <= dates["expire_fixed_date"]:
            fixed_date_status = Status.ACTIVE
        elif dates["expire_fixed_date"] < today <= dates["terminate_fixed_date"]:
            fixed_date_status = Status.EXPIRED
        else:
            fixed_date_status = Status.TERMINATE
    else:
        fixed_date_status = Status.ACTIVE

    # TODO fix this mess
    status, reason = {
        (Status.ACTIVE, Status.ACTIVE): (Status.ACTIVE, None),
        (Status.EXPIRED, Status.ACTIVE): (Status.EXPIRED, Reason.ACCESS_EXPIRED),
        (Status.ACTIVE, Status.EXPIRED): (Status.EXPIRED, Reason.DATE_EXPIRED),
        (Status.EXPIRED, Status.EXPIRED): (Status.EXPIRED, Reason.BOTH_EXPIRED),
        (Status.TERMINATE, Status.ACTIVE): (Status.TERMINATE, Reason.ACCESS_EXPIRED),
        (Status.ACTIVE, Status.TERMINATE): (Status.TERMINATE, Reason.DATE_EXPIRED),
        (Status.TERMINATE, Status.EXPIRED): (Status.TERMINATE, Reason.BOTH_EXPIRED),
        (Status.EXPIRED, Status.TERMINATE): (Status.TERMINATE, Reason.BOTH_EXPIRED),
        (Status.TERMINATE, Status.TERMINATE): (Status.TERMINATE, Reason.BOTH_EXPIRED),
    }[(lab_status, fixed_date_status)]

    return status, reason


def get_storage_info(item: StorageItem) -> StorageInfo:
    dates = get_dates(item)
    status, reason = check_status(dates)

    today = date.today()
    messages = []
    for message in item.storage_messages:
        if (today - message.message_at).days < dates["days_after_expiration"]:
            messages.append(dt_to_str(message))

    return {  # TODO Fix this
        "item_label_id": item.item_label_id,
        "member_number": item.member.member_number,
        "name": f"{item.member.firstname} {item.member.lastname or ''}",
        "storage_type": item.storage_type,
        "days_after_expiration": dates["days_after_expiration"],
        "status": status,
        "reason": reason,
        "messages": messages,
        "last_check_at": dt_to_str(item.last_check_at),
    }


def get_item_from_label_id(item_label_id: int) -> StorageItem | None:
    return (
        db_session.query(StorageItem)
        .filter(StorageItem.item_label_id == item_label_id)
        .join(StorageType, StorageItem.storage_type_id)
        .join(Member, StorageItem.member_id)
        .one_or_none()
    )


def store_message(item: StorageItem, message_type: StorageMessageType) -> None:
    message = StorageMessage(
        member_id=item.member_id,
        item_label_id=item.item_label_id,
        message_at=datetime.utcnow(),
        message_type=message_type,
    )
    db_session.add(message)
    db_session.flush()


def send_message_about_storage(
    member_number: int,
    item_label_id: int,
    message_type: StorageMessageType,
    description: str,
    storage_type: StorageType,
    fixed_end_date: Optional[datetime],
) -> None:
    item = get_item_from_label_id(item_label_id)
    if item is None:
        raise NotFound(f"Storage item, {item_label_id}, for member number {member_number} not found")

    dates = get_dates(item)
    status, reason = check_status(dates)

    if item.storage_type.has_fixed_end_date:
        try:
            template = {
                (
                    "message-warning",
                    Reason.ACCESS_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_WARNING_LAB,
                (
                    "message-last-warning",
                    Reason.ACCESS_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_WARNING_LAB,
                (
                    "message-terminated",
                    Reason.ACCESS_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_TERMINATED_LAB,
                (
                    "message-warning",
                    Reason.DATE_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_WARNING_DATE,
                (
                    "message-last-warning",
                    Reason.DATE_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_WARNING_DATE,
                (
                    "message-terminated",
                    Reason.DATE_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_TERMINATED_DATE,
                (
                    "message-warning",
                    Reason.BOTH_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_WARNING_BOTH,
                (
                    "message-last-warning",
                    Reason.BOTH_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_WARNING_BOTH,
                (
                    "message-terminated",
                    Reason.BOTH_EXPIRED,
                ): MessageTemplate.TEMP_STORAGE_TERMINATED_BOTH,
            }[(message_type, reason)]
        except KeyError:
            raise BadRequest(f"Bad message type {message_type}")
    else:
        try:
            template = {
                "message-warning": MessageTemplate.BOX_WARNING,
                "message-last-warning": MessageTemplate.BOX_FINAL_WARNING,
                "message-terminated": MessageTemplate.BOX_TERMINATED,
            }[message_type]
        except KeyError:
            raise BadRequest(f"Bad message type {message_type}")

    if item.storage_type.has_fixed_end_date:
        send_message(
            template,
            item.member,
            expiration_time=EXPIRATION_TIME,
            labaccess_end_date=date_to_str(dates["expire_lab_date"]),
            fixed_end_date=date_to_str(dates["fixed_end_date"]),
            to_termination_days=dates["to_termination_days"],
            days_after_expiration=dates["days_after_expiration"],
            description=description,
        )
    else:
        send_message(
            template,
            item.member,
            expiration_time=EXPIRATION_TIME,
            labaccess_end_date=date_to_str(dates["expire_lab_date"]),
            to_termination_days=dates["to_termination_days"],
            days_after_expiration=dates["days_after_expiration"],
        )

    store_message(item, message_type)


def fetch_storage_item(
    member_number: int,
    item_label_id: int,
    storage_type: StorageType,
    fixed_end_date: datetime,
) -> StorageInfo:
    item = get_item_from_label_id(item_label_id)
    if item is not None:
        found_item = True
        if storage_type != item.storage_type:
            raise BadRequest("Storage type argument does not match storage type in db.")
        if item.storage_type:  # TODO has fixed end date check
            if item.fixed_end_date is None:
                raise BadRequest("Fixed end date is missing in db.")
            if fixed_end_date != item.fixed_end_date:
                raise BadRequest("Fixed end date does not match fixed end date in db.")
    else:
        found_item = False
        try:
            # Find the member since there was nothing in the db with the item_label_id
            member = db_session.query(Member).filter(Member.member_number == member_number).one()
        except NoResultFound:
            raise NotFound(f"Member not found {member_number}")
        item = StorageItem(
            member_id=member.member_id,
            item_label_id=item_label_id,
            storage_type=storage_type,
            fixed_end_date=fixed_end_date,
        )

    item.last_check_at = datetime.utcnow()
    if not found_item:
        db_session.add(item)
    db_session.commit()

    return get_storage_info(item)


# TODO exceptions should probably return some error instead of exception?
