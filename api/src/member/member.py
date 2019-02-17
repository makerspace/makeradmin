from datetime import datetime
from urllib.parse import quote_plus

from flask import render_template
from sqlalchemy.orm.exc import NoResultFound

from core.auth import create_access_token
from membership.models import Member
from messages.views import message_entity
from service import config
from service.db import db_session
from service.error import NotFound
from service.logging import logger
from service.util import format_datetime


def send_access_token_email(redirect, user_tag, ip, browser):
    try:
        if user_tag.isdigit():
            member_id, = db_session.query(Member.member_id).filter_by(member_number=int(user_tag)).one()
        else:
            member_id, = db_session.query(Member.member_id).filter_by(email=user_tag).one()
            
    except NoResultFound:
        raise NotFound(f"Could not find user by '{user_tag}'.", fields='user_tag')

    access_token = create_access_token(ip, browser, member_id)['access_token']

    url = config.get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))

    logger.info(f"sending login link {url!r} to member_id {member_id}")
    
    message_entity.create_message({
        "recipients": [
            {
                "type": "member",
                "id": member_id
            },
        ],
        "message_type": "email",
        "title": f"Log in to MakerAdmin ({format_datetime(datetime.now())})",
        "description": render_template("email_login.html", url=url)
    })

    return {"status": "sent"}


# @instance.route("current", methods=["GET"], permission='user')
# def current_member() -> str:
#     user_id = assert_get(request.headers, "X-User-Id")
#     return instance.gateway.get("membership/member/%s" % user_id).text
#
#
# @instance.route("current/permissions", methods=["GET"], permission='user')
# @route_helper
# def permissions() -> Dict[str, Any]:
#     user_id = assert_get(request.headers, "X-User-Id")
#     permissionsStr = request.headers["X-User-Permissions"].strip() if "X-User-Permissions" in request.headers else ""
#     permissions = permissionsStr.split(",") if permissionsStr != "" else []
#     return {
#         "member_id": user_id,
#         "permissions": permissions,
#     }
#
#
# @instance.route("current/membership", methods=["GET"], permission='user')
# def membership_info() -> str:
#     ''' If the user has lab access and how long '''
#     user_id = assert_get(request.headers, "X-User-Id")
#     return instance.gateway.get(f"membership/member/{user_id}/membership").text
#
#
# instance.serve_indefinitely()
