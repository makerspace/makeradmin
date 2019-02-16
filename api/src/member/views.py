from flask import request

from member import service
from service.api_definition import POST, PUBLIC, Arg
from service.db import db_session


@service.route("/send_access_token", method=POST, permission=PUBLIC)
def send_access_token(redirect=Arg(str), user_tag: str=Arg(str)):
    redirect = redirect or "/member"

    if user_tag.isdigit():
        db_session.execute("SELECT member_id FROM membership_members WHERE member_number = %s", (user_tag,))
    else:
        db_session.execute("SELECT member_id FROM membership_members WHERE email=%s", (user_tag,))
        
    matching = cur.fetchall()
    if len(matching) == 0:
        abort(400, "not found")
    if len(matching) > 1:
        abort(400, "ambiguous")
    user_id = matching[0][0]

    response = instance.gateway.post("oauth/force_token", {"user_id": user_id}).json()
    token = response["access_token"]
    url = instance.gateway.get_public_url(f"/member/login/{token}?redirect=" + urllib.parse.quote_plus(redirect))
    logger.info(f"sending login link {url!r} to user_id {user_id}")
    r = instance.gateway.post("messages/message", {
        "recipients": [
            {
                "type": "member",
                "id": user_id
            },
        ],
        "message_type": "email",
        "title": f"Log in to MakerAdmin ({format_datetime(datetime.now())})",
        "description": render_template("email_login.html", url=url)
    })
    if not r.ok:
        raise Exception(r.text)

    return jsonify({"status": "sent"})


@instance.route("current", methods=["GET"], permission='user')
def current_member() -> str:
    user_id = assert_get(request.headers, "X-User-Id")
    return instance.gateway.get("membership/member/%s" % user_id).text


@instance.route("current/permissions", methods=["GET"], permission='user')
@route_helper
def permissions() -> Dict[str, Any]:
    user_id = assert_get(request.headers, "X-User-Id")
    permissionsStr = request.headers["X-User-Permissions"].strip() if "X-User-Permissions" in request.headers else ""
    permissions = permissionsStr.split(",") if permissionsStr != "" else []
    return {
        "member_id": user_id,
        "permissions": permissions,
    }


@instance.route("current/membership", methods=["GET"], permission='user')
def membership_info() -> str:
    ''' If the user has lab access and how long '''
    user_id = assert_get(request.headers, "X-User-Id")
    return instance.gateway.get(f"membership/member/{user_id}/membership").text


instance.serve_indefinitely()
