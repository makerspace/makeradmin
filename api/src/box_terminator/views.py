from flask import g
from box_terminator import service

from service.api_definition import GET, Arg, MEMBER_EDIT, POST, symbol, PUBLIC
import json


@service.route("/fetch/<string:message>", method=GET, permission=MEMBER_EDIT)
def box_terminator_fetch(
    message
    # message=Arg(str)
):
    """Used when scanning qr codes."""
    ParsedScannedMessage = json.loads(message)
    if ( "member_number" in ParsedScannedMessage ):
        if ( not "type" in ParsedScannedMessage ) or ParsedScannedMessage['type'] == 'box':
            return json.dumps({
                "type": "box",
                "member_number": ParsedScannedMessage['member_number'],
                "member_name": "Test Testsson",
                "expired": False,
                "expired_date": "2020-01-01",
                "info": "last nagged 2023-09-09",
                "options": [
                    "nag", "terminate"
                ]
                
            })
        else:
            return ParsedScannedMessage['type']


@service.route("/test", method=GET, permission=PUBLIC)
def box_terminator_nag_route():
    """Send a nag email for this box."""
    return "test"