from flask import Flask, request, abort, jsonify, render_template
import service
from service import eprint, assert_get, route_helper
import urllib.parse
from typing import Dict, Any


instance = service.create(name="Makerspace Member Login", url="member", port=80, version="1.0")

# Grab the database so that we can use it inside requests
db = instance.db


@instance.route("send_access_token", methods=["POST"], permission=None)
def send_access_token():
    data = request.get_json()
    if data is None:
        abort(400, "missing json")

    redirect = "member"
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

    # This should be sent via an email, but lets just return it for now
    response = instance.gateway.post("oauth/force_token", {"user_id": user_id}).json()
    token = response["access_token"]
    url = instance.gateway.get_frontend_url(f"member/login/{token}?redirect=" + urllib.parse.quote_plus(redirect))

    r = instance.gateway.post("messages", {
        "recipients": [
            {
                "type": "member",
                "id": user_id
            },
        ],
        "message_type": "email",
        "subject": "Log in to MakerAdmin",
        "body": render_template("email_login.html", url=url)
    })
    if not r.ok:
        raise Exception(r.text)

    return jsonify({"status": "sent"})


@instance.route("current", methods=["GET"], permission=None)
def current_member() -> str:
    user_id = assert_get(request.headers, "X-User-Id")
    return instance.gateway.get("membership/member/%s" % user_id).text


@instance.route("current/permissions", methods=["GET"], permission=None)
@route_helper
def permissions() -> Dict[str,Any]:
    user_id = assert_get(request.headers, "X-User-Id")
    permissionsStr = request.headers["X-User-Permissions"].strip() if "X-User-Permissions" in request.headers else ""
    permissions = permissionsStr.split(",") if permissionsStr != "" else []
    return {
        "member_id": user_id,
        "permissions": permissions,
    }

@instance.route("current/membership", methods=["GET"], permission=None)
def membership_info() -> str:
    ''' If the user has lab access and how long '''
    user_id = assert_get(request.headers, "X-User-Id")
    return instance.gateway.get(f"membership/member/{user_id}/membership").text

instance.serve_indefinitely()
