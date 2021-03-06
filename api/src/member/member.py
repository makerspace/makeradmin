from datetime import datetime
from urllib.parse import quote_plus

from core.auth import create_access_token, get_member_by_user_identification
from messages.message import send_message
from messages.models import MessageTemplate
from service import config
from service.logging import logger
from service.util import format_datetime


def send_access_token_email(redirect, user_identification, ip, browser):
    member = get_member_by_user_identification(user_identification)

    access_token = create_access_token(ip, browser, member.member_id)['access_token']

    url = config.get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))

    logger.info(f"sending login link {url!r} to member_id {member.member_id}")

    send_message(
        MessageTemplate.LOGIN_LINK, member,
        url=url,
        now=format_datetime(datetime.now()),
    )

    return {"status": "sent"}
