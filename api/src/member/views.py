from flask import request, g

from member import service
from member.member import send_access_token_email
from membership.views import member_entity
from service.api_definition import POST, PUBLIC, Arg, GET, USER


@service.route("/send_access_token", method=POST, permission=PUBLIC)
def send_access_token(redirect=Arg(str, required=False), user_tag: str=Arg(str)):
    """ Send access token email to user with username or member_number user_tag. """
    return send_access_token_email(redirect or "/member", user_tag, request.remote_addr, request.user_agent.string)


@service.route("/current", method=GET, permission=USER)
def current_member():
    """ Get current member. """
    return member_entity.read(g.user_id)
