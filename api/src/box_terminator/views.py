import json

from flask import g
from service.api_definition import GET, MEMBER_EDIT
from service.error import BadRequest, NotFound

from box_terminator import service
from box_terminator.box_terminator import fetch_storage_item, send_message_about_storage, terminate_storage_item
from box_terminator.models import MessageType, StorageType


@service.route("/fetch/<string:message>", method=GET, permission=MEMBER_EDIT)
def box_terminator_fetch(message):
    """Used when scanning qr codes."""
    ParsedScannedMessage = json.loads(message)
    fetch_storage_item(
        ParsedScannedMessage.box_id,
        ParsedScannedMessage.member_number,
        ParsedScannedMessage.type,
        ParsedScannedMessage.expirey_date,
        ParsedScannedMessage.unix_timestamp,
        ParsedScannedMessage.description,
    )
    # What should be returned.
    # if "member_number" in ParsedScannedMessage:
    #     if (not "type" in ParsedScannedMessage) or ParsedScannedMessage["type"] == "box":
    #         return json.dumps(
    #             {
    #                 "type": "box",
    #                 "member_number": ParsedScannedMessage["member_number"],
    #                 "member_name": "Test Testsson",
    #                 "expired": False,
    #                 "expired_date": "2024-09-09",
    #                 "info": "last nagged 2023-09-09",
    #                 "storage_id": 1,
    #             }
    #         )
    #     else:
    #         nagButton = {"text": "nag", "path": "nag", "color": "#FF0000"}
    #         terminateButton = {"text": "Terminate", "path": "terminate", "color": "#FF0000"}
    #         return json.dumps(
    #             {
    #                 "type": "temp storage",
    #                 "member_number": ParsedScannedMessage["member_number"],
    #                 "member_name": "Test Testsson",
    #                 "expired": True,
    #                 "expired_date": "2020-01-01",
    #                 "info": "last nagged 2023-09-09",
    #                 "storage_id": 1,
    #                 "options": [
    #                     nagButton,
    #                     terminateButton,
    #                 ],
    #             }
    #         )


# TODO route for memberbooth to fetch storage types


@service.route("/action/<string:action>/<string:storage_id>", method=GET, permission=MEMBER_EDIT)
def box_terminator_nag_route(
    action,
    storage_id,
):
    """Send a nag email for this box."""
    return send_message_about_storage(action, storage_id)
