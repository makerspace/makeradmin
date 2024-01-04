import json

from flask import g
from service.api_definition import GET, MEMBER_EDIT, POST, PUBLIC, Arg, symbol

from box_terminator import service


@service.route("/fetch/<string:message>", method=GET, permission=MEMBER_EDIT)
def box_terminator_fetch(
    message,
    # message=Arg(str)
):
    """Used when scanning qr codes."""
    ParsedScannedMessage = json.loads(message)
    if "member_number" in ParsedScannedMessage:
        if (not "type" in ParsedScannedMessage) or ParsedScannedMessage["type"] == "box":
            return json.dumps(
                {
                    "type": "box",
                    "member_number": ParsedScannedMessage["member_number"],
                    "member_name": "Test Testsson",
                    "expired": False,
                    "expired_date": "2024-09-09",
                    "info": "last nagged 2023-09-09",
                    "box_id": 1,
                }
            )
        else:
            return json.dumps(
                {
                    "type": "temp storage",
                    "member_number": ParsedScannedMessage["member_number"],
                    "member_name": "Test Testsson",
                    "expired": True,
                    "expired_date": "2020-01-01",
                    "info": "last nagged 2023-09-09",
                    "box_id": 1,
                    "options": [
                        {"text": "nag", "path": "nag", "color": "#FF0000"},
                        {"text": "Terminate", "path": "terminate", "color": "#FF0000"},
                    ],
                }
            )


@service.route("/action/<string:action>/<string:box_id>", method=GET, permission=PUBLIC)
def box_terminator_nag_route(
    action,
    box_id,
):
    """Send a nag email for this box."""
    if action == "nag":
        return "Nag sent"
    elif action == "terminate":
        return "Box terminated"
