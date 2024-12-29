from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List
from urllib.parse import quote_plus

import markdown
from core.auth import create_access_token, get_member_by_user_identification
from membership.models import Group, Member
from membership.views import group_entity
from messages.message import send_message
from messages.models import MessageTemplate
from service import config
from service.db import db_session
from service.error import BadRequest
from service.logging import logger
from service.util import format_datetime
from sqlalchemy.exc import DataError


def send_access_token_email(redirect, user_identification, ip, browser):
    member = get_member_by_user_identification(user_identification)

    access_token = create_access_token(ip, browser, member.member_id)["access_token"]

    url = config.get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))

    logger.info(f"sending login link {url!r} to member_id {member.member_id}")

    send_message(
        MessageTemplate.LOGIN_LINK,
        member,
        url=url,
        now=format_datetime(datetime.now(timezone.utc).replace(tzinfo=None)),
    )

    return {"status": "sent"}


def send_updated_member_info_email(member_id: int, msg_swe: str, msg_en: str):
    member = db_session.get(Member, member_id)

    logger.info(
        f"sending email about updated personal information to member_id {member.member_id} with message {msg_en=},"
        f" {msg_swe=}"
    )

    send_message(
        MessageTemplate.UPDATED_MEMBER_INFO,
        member,
        now=format_datetime(datetime.now(timezone.utc).replace(tzinfo=None)),
        message_swe=msg_swe,
        message_en=msg_en,
    )

    return {"status": "sent"}


def set_pin_code(member_id: int, pin_code: str):
    member: Member = db_session.get(Member, member_id)
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


def _get_file_content_as_html(path: Path):
    file_content = path.read_text("utf-8")
    if path.suffix == ".md":
        return markdown.markdown(file_content)
    return file_content


def get_license_html_text() -> str:
    repo_root = Path(__file__).parent / "../.."
    readme_path = repo_root / "data/licenses/README.md"
    html_files = list(repo_root.glob("data/licenses/*.html"))
    md_files = list(repo_root.glob("data/licenses/*.md"))

    no_licenses_added = (html_files + md_files) == [readme_path]
    if no_licenses_added:
        return _get_file_content_as_html(readme_path)

    all_files_to_render = [f for f in html_files + md_files if f != readme_path]
    combined_file_content = [_get_file_content_as_html(f) for f in all_files_to_render]

    return "\n".join(combined_file_content)
