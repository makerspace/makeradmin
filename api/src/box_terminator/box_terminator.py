from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

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

from box_terminator.models import StorageAction, StorageItem, StorageMessage, StorageType

JUDGMENT_DAY = datetime(1997, 9, 26)  # Used as default for missing lab access date
EXPIRATION_TIME = 45  # Number of days from expiration date to the termination date when the item is removed
FUTURE_LIMIT = 90  # Maximum number of days possible for fixed_end_date


class Status(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATE = "terminate"


class StorageAction(Enum):
    TERMINATE = "terminate"
    NAG = "nag"

    def to_button(self) -> Dict[str, str]:
        if self == StorageAction.TERMINATE:
            color = "#FF0000"
        elif self == StorageAction.NAG:
            color = "#FFFF00"
        else:
            color = "#35B3EE"
        return {"text": self.value, "path": self.value, color: color}


@dataclass
class StorageInfo:
    member_name: str
    member_number: str
    storage_item: StorageItem
    status: Status
    expiration_date: date
    expired_reasons: List[str]
    actions: List[StorageAction]

    def to_dict(self) -> Dict:
        # The info text is fairly generic in what it can be
        info_text = ""  # TODO display some nag history here

        expired = self.status != Status.ACTIVE
        options = [action.to_button() for action in self.actions]
        return {
            "type": self.item.storage_type.storage_type,
            "member_number": self.member_number,
            "member_name": self.member_name,
            "expired": expired,
            "expired_date": self.expiration_date,
            "storage_id": self.item.id,
            "options": options,
            "info": info_text,
        }


def get_expiration_date_from_end_date(expiration_date: datetime) -> datetime:
    return expiration_date + timedelta(days=EXPIRATION_TIME)


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
    terminate_lab_date = get_expiration_date_from_end_date(expire_lab_date)

    if item.storage_type.has_fixed_end_date:
        fixed_end_date = item.fixed_end_date
        terminate_fixed_date = get_expiration_date_from_end_date(fixed_end_date)

        to_termination_days = min((terminate_fixed_date - today).days, (terminate_lab_date - today).days)
        days_after_expiration = max((today - fixed_end_date).days, (today - expire_lab_date).days)
    else:
        fixed_end_date = None
        terminate_fixed_date = None

        to_termination_days = (terminate_lab_date - today).days
        days_after_expiration = (today - expire_lab_date).days

    pending_labaccess_days = pending_action_value_sum(item.member_id, ProductAction.ADD_LABACCESS_DAYS)

    return {  # TODO change to a dataclass
        "expire_lab_date": expire_lab_date,
        "terminate_lab_date": terminate_lab_date,
        "expire_fixed_date": fixed_end_date,
        "terminate_fixed_date": terminate_fixed_date,
        "to_termination_days": to_termination_days,
        "days_after_expiration": days_after_expiration,
        "pending_labaccess_days": pending_labaccess_days,
    }


def get_date_status(dates: Dict[str, datetime]) -> Dict[str, Status]:
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

    return {"labacces": lab_status, "fixed_date": fixed_date_status}


def check_status(status_per_check: Dict[str, Status]) -> Tuple[Status, List[str]]:
    reasons_per_check_status: Dict[Status, List[str]] = []
    for check_type, check_status in status_per_check.items():
        if check_status in reasons_per_check_status:
            reasons_per_check_status[check_status].append(check_type)
        else:
            reasons_per_check_status[check_status] = [check_type]

    if Status.TERMINATE in reasons_per_check_status:
        status_to_return = Status.TERMINATE
    elif Status.EXPIRED in reasons_per_check_status:
        status_to_return = Status.EXPIRED
    else:
        status_to_return = Status.ACTIVE

    return status_to_return, reasons_per_check_status[status_to_return]


def get_storage_actions(type: StorageType, dates: Dict[str, datetime], status: Status) -> List[StorageAction]:
    actions: List[StorageAction] = []

    if status == Status.TERMINATE:
        actions.append(StorageAction.TERMINATE)
    elif status == Status.EXPIRED:
        actions.append(StorageAction.NAG)

    return actions


def get_storage_info(item: StorageItem) -> StorageInfo:
    dates = get_dates(item)
    expiration_date = max(dates.values)
    status_per_check = get_date_status(dates)
    status, expired_reasons = check_status(status_per_check)

    actions = get_storage_actions(item.storage_type, dates, status)

    member_name = f"{item.member.first_name} {item.member.last_name}"

    return StorageInfo(
        member_name=member_name,
        storage_item=item,
        status=status,
        expiration_date=expiration_date,
        expired_reasons=expired_reasons,
        actions=actions,
    )


def get_item_from_label_id(item_label_id: int) -> StorageItem | None:
    return (
        db_session.query(StorageItem)
        .filter(StorageItem.item_label_id == item_label_id)
        .join(StorageType, StorageItem.storage_type_id)
        .join(Member, StorageItem.member_id)
        .one_or_none()
    )


def store_message(item: StorageItem, storage_action: StorageAction) -> None:
    message = StorageMessage(
        member_id=item.member_id,
        item_label_id=item.item_label_id,
        message_at=datetime.utcnow(),
        storage_action=storage_action,
    )
    db_session.add(message)
    db_session.flush()


def send_message_about_storage(item_label_id: int, storage_action: StorageAction) -> None:
    item = get_item_from_label_id(item_label_id)
    if item is None:
        raise NotFound(f"Storage item {item_label_id}  not found")

    dates = get_dates(item)

    template = storage_action.email_template  # TODO str to the enum

    send_message(
        template,
        item.member,
        expiration_time=EXPIRATION_TIME,
        labaccess_end_date=date_to_str(dates["expire_lab_date"]),
        fixed_end_date=date_to_str(dates["fixed_end_date"]),
        to_termination_days=dates["to_termination_days"],
        days_after_expiration=dates["days_after_expiration"],
        description=item.members_description,
    )

    store_message(item, storage_action)


def fetch_storage_item(item_label_id: int) -> StorageInfo:
    item = get_item_from_label_id(item_label_id)
    if item is None:
        # TODO create the item in the db instead
        raise NotFound(f"Storage item, {item_label_id}, not found")

    item.last_check_at = datetime.utcnow()
    db_session.commit()
    return get_storage_info(item)


# TODO exceptions should probably return some error instead of exception?
