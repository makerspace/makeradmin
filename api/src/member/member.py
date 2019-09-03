from datetime import datetime
from urllib.parse import quote_plus

from sqlalchemy.orm.exc import NoResultFound

from core.auth import create_access_token
from membership.models import Member
from messages.message import send_message
from messages.models import MessageTemplate
from service import config
from service.db import db_session
from service.error import NotFound
from service.logging import logger
from service.util import format_datetime


def send_access_token_email(redirect, user_tag, ip, browser):
    try:
        if user_tag.isdigit():
            member = db_session.query(Member).filter_by(member_number=int(user_tag)).one()
        else:
            member = db_session.query(Member).filter_by(email=user_tag).one()
            
    except NoResultFound:
        raise NotFound(f"Could not find any user with the name or email '{user_tag}'.", fields='user_tag',
                       status="not found")

    access_token = create_access_token(ip, browser, member.member_id)['access_token']

    url = config.get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))

    logger.info(f"sending login link {url!r} to member_id {member.member_id}")

    send_message(
        MessageTemplate.LOGIN_LINK, member,
        url=url,
        now=format_datetime(datetime.now()),
    )

    return {"status": "sent"}
