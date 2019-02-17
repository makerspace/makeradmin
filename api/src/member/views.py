from flask import request

from member import service
from member.member import send_access_token_email
from service.api_definition import POST, PUBLIC, Arg


@service.route("/send_access_token", method=POST, permission=PUBLIC)
def send_access_token(redirect=Arg(str, required=False), user_tag: str=Arg(str)):
    """ Send access token email to user with username or member_number user_tag. """
    return send_access_token_email(redirect or "/member", user_tag, request.remote_addr, request.user_agent.string)
