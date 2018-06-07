from flask import Flask, request, abort, jsonify, render_template
import service
from service import eprint, assert_get

instance = service.create(name="Makerspace Member Login", url="member", port=80, version="1.0")

# Grab the database so that we can use it inside requests
db = instance.db


@instance.route("send_access_token", methods=["POST"], permission=None)
def send_access_token():
    data = request.get_json()
    if data is None:
        abort(400, "missing json")

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
    url = instance.gateway.get_frontend_url("member/login/" + token)

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
def current_member():
    user_id = assert_get(request.headers, "X-User-Id")
    return instance.gateway.get("membership/member/%s" % user_id).text


@instance.route("current/keys", methods=["GET"], permission=None)
def key_info():
    ''' List of keys that the current logged in member has '''
    user_id = assert_get(request.headers, "X-User-Id")
    return instance.gateway.get("related?param=/membership/member/%s&matchUrl=/keys/(.*)&from=keys&page=1&sort_by=&sort_order=asc&per_page=10000" % user_id).text


instance.serve_indefinitely()
