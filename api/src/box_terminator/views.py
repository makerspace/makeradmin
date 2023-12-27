from flask import g

from multiaccess import service  # TODO fix maybe?
from box_terminator.box_terminator import (
    send_message_about_storage,
    terminate_storage_item,
    fetch_storage_item,
)
from service.api_definition import GET, Arg, MEMBER_EDIT, POST, symbol
from service.error import NotFound, BadRequest
from box_terminator.models import MessageType, StorageType


@service.route("/box_terminator/message", method=POST, permission=MEMBER_EDIT)
def box_terminator_message(
    member_number=Arg(int), box_label_id=Arg(int), message_type_str=Arg(symbol), storage_type_str=Arg(symbol)
):
    """Send a some sort of message for this stored item."""

    message_type = db_session.query(MessageType).filter(MessageType.message_type == message_type_str).one_or_none()
    if message_type is None:
        raise NotFound(f"Message type, {message_type_str}, not found")
    storage_type = db_session.query(StorageType).filter(StorageType.message_type == storage_type_str).one_or_none()
    if storage_type is None:
        raise NotFound(f"Storage type, {storage_type_str}, not found")

    return send_message_about_storage(member_number, box_label_id, message_type, storage_type)


@service.route("/box-terminator/fetch", method=POST, permission=MEMBER_EDIT)
def box_terminator_fetch(
    member_number=Arg(int),
    item_label_id=Arg(int),
    storage_type=Arg(symbol),
    fixed_end_date=Arg(iso_date, False),
):
    """Used when scanning qr codes."""
    # Arg(isodate) converts from isoformat string to datetime
    return fetch_storage_item(member_number, item_label_id, storage_type, fixed_end_date)


# TODO route for memberbooth to fetch storage types
