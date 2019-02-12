from flask import request, jsonify, render_template
from backend_service import assert_get, route_helper, create, abort, format_datetime
import urllib.parse
from typing import Dict, Any
from logging import getLogger
from datetime import datetime

logger = getLogger('makeradmin')

instance = create(name="member", url="member", port=80, version="1.0")

# Grab the database so that we can use it inside requests
db = instance.db


@instance.route("send_access_token", methods=["POST"], permission=None)
def send_access_token():
    data = request.get_json()
    if data is None:
        abort(400, "missing json")

    redirect = "/member"
    if "redirect" in data:
        redirect = data["redirect"]

    user_tag = assert_get(data, "user_tag")
    with db.cursor() as cur:
        if user_tag.isdigit():
            cur.execute("SELECT member_id FROM membership_members WHERE member_number=%s", (user_tag,))
        else:
            cur.execute("SELECT member_id FROM membership_members WHERE email=%s", (user_tag,))
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
