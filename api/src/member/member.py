from datetime import datetime
from typing import Any, List
from urllib.parse import quote_plus
from sqlalchemy.exc import DataError

from core.auth import create_access_token, get_member_by_user_identification
from membership.models import Member, Group
from messages.message import send_message
from messages.models import MessageTemplate
from service import config
from service.db import db_session
from service.error import BadRequest
from service.logging import logger
from service.util import format_datetime
from membership.views import group_entity


def send_access_token_email(redirect, user_identification, ip, browser):
    member = get_member_by_user_identification(user_identification)

    access_token = create_access_token(ip, browser, member.member_id)["access_token"]

    url = config.get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))

    logger.info(f"sending login link {url!r} to member_id {member.member_id}")

    send_message(
        MessageTemplate.LOGIN_LINK,
        member,
        url=url,
        now=format_datetime(datetime.now()),
    )

    return {"status": "sent"}


def set_pin_code(member_id: int, pin_code: str):
    member: Member = db_session.query(Member).get(member_id)
    member.pin_code = pin_code

    try:
        db_session.flush()
    except DataError:
        logger.exception(f"Could not set PIN code to {pin_code!r}")
        raise BadRequest(f"PIN code is of wrong format. Make sure it is maximum 30 characters long.")

    return {"status": "PIN code changed"}


def get_member_groups(member_id: int) -> List[Any]:
    groups = (
        db_session.query(Group)
        .join(Member.groups)
        .filter(Member.member_id == member_id)
        .filter(Group.deleted_at == None)
        .all()
    )
    return [group_entity.to_obj(g) for g in groups]
