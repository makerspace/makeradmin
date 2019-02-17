from flask import request, g

from member import service
from member.member import send_access_token_email
from membership.member_auth import get_member_permissions
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


@service.route("/current/permissions", method=GET, permission=USER)
def current_permissions():
    """ Get current member permissions. """
    return {
        "permissions": [p for _, p in get_member_permissions(g.user_id)],
    }

    
# def permissions() -> Dict[str, Any]:
#     user_id = assert_get(request.headers, "X-User-Id")
#     permissionsStr = request.headers["X-User-Permissions"].strip() if "X-User-Permissions" in request.headers else ""
#     permissions = permissionsStr.split(",") if permissionsStr != "" else []
#     return {
#         "member_id": user_id,
#         "permissions": permissions,
#     }
#

