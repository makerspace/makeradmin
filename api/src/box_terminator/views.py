import json

from service.api_definition import GET, MEMBER_EDIT, PUBLIC

from box_terminator import service


# The following routes are just mocks, needs to be implemented properly
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
                    "info": "last nagged 2023-09-09\nThis is a new line",
                    "storage_id": 1,
                }
            )
        else:
            nagButton = {"text": "nag", "path": "nag", "color": "#FF0000"}
            terminateButton = {"text": "Terminate", "path": "terminate", "color": "#FF0000"}
            return json.dumps(
                {
                    "type": "temp storage",
                    "member_number": ParsedScannedMessage["member_number"],
                    "member_name": "Test Testsson",
                    "expired": True,
                    "expired_date": "2020-01-01",
                    "info": "last nagged 2023-09-09",
                    "storage_id": 1,
                    "options": [
                        nagButton,
                        terminateButton,
                    ],
                }
            )


@service.route("/action/<string:action>/<string:storage_id>", method=GET, permission=PUBLIC)
def box_terminator_nag_route(
    action,
    storage_id,
):
    """Send a nag email for this box."""
    if action == "nag":
        return "Nag sent"
    elif action == "terminate":
        return "Box terminated"
