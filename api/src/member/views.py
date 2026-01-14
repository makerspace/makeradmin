import serde
from change_phone_request import change_phone_request, change_phone_validate
from flask import g, request
from membership.member_auth import get_member_permissions
from membership.membership import get_access_summary, get_membership_summary
from membership.models import Member
from membership.views import member_entity
from multiaccess.memberbooth import get_member_labels
from quiz.views import member_quiz_statistics
from service.api_definition import GET, MESSAGE_SEND, POST, PUBLIC, USER, Arg, natural1, non_empty_str
from service.db import db_session
from service.error import Unauthorized
from sqlalchemy import select
from tasks.models import MemberPreference, MemberPreferenceQuestionType

from member import service
from member.member import (
    get_license_html_text,
    get_member_groups,
    send_access_token_email,
    send_updated_member_info_email,
    set_pin_code,
)


@service.route("/send_access_token", method=POST, permission=PUBLIC)
def send_access_token(redirect=Arg(str, required=False), user_identification: str = Arg(str)):
    """Send access token email to user with username or member_number user_identification."""
    return send_access_token_email(
        redirect or "/member", user_identification, request.remote_addr, request.user_agent.string
    )


@service.route("/send_updated_member_info", method=POST, permission=MESSAGE_SEND)
def send_updated_member_info(member_id: int = Arg(int), msg_swe: str = Arg(str), msg_en: str = Arg(str)):
    """Send email to user with information that personal information has been updated."""
    return send_updated_member_info_email(member_id, msg_swe, msg_en)


@service.route("/current", method=GET, permission=USER)
def current_member():
    """Get current member."""
    m = member_entity.read(g.user_id)

    # Expose if the member has a password set, but not what the password is (not even the hash)
    assert m is not None
    m2 = db_session.get(Member, g.user_id)
    assert m2 is not None
    m["has_password"] = m2.password is not None

    return m


@service.route("/current/permissions", method=GET, permission=USER)
def current_permissions():
    """Get current member permissions."""
    return {"permissions": [p for _, p in get_member_permissions(g.user_id)]}


@service.route("/current/membership", method=GET, permission=USER)
def current_membership_info():
    """Get current user membership information."""
    return get_membership_summary(g.user_id).as_json()


@service.route("/current/access", method=GET, permission=USER)
def current_access_info():
    """Get current user accessy information."""
    return get_access_summary(g.user_id)


@service.route("/current/groups", method=GET, permission=USER)
def current_membership_groups():
    return get_member_groups(g.user_id)


@service.route("/current/quizzes", method=GET, permission=USER)
def current_member_quiz_info():
    """Get info about which quizzes the current user has completed."""
    return member_quiz_statistics(g.user_id)


@service.route("/current/labels", method=GET, permission=USER)
def current_member_labels() -> dict:
    """Get info about which labels the current user has."""
    return serde.to_dict(get_member_labels(g.user_id))


@service.route("/current/set_pin_code", method=POST, permission=USER)
def set_pin_code_endpoint(pin_code=Arg(str)):
    return set_pin_code(g.user_id, pin_code)


@service.route("/send_phone_number_validation_code", method=POST, permission=PUBLIC)
def request_change_phone_number(member_id: int | None = Arg(int, required=False), phone=Arg(non_empty_str)):
    if member_id is not None and member_id != g.user_id:
        raise Unauthorized("You can only change your own phone number.")
    return change_phone_request(member_id, phone)


@service.route("/current/slack_status", method=GET, permission=USER)
def get_slack_status():
    """Get Slack account status and task delegation preference for the current member."""
    from service.config import config
    from slack.util import lookup_slack_user_by_email
    from slack_sdk import WebClient
    from tasks.delegate import is_task_delegation_enabled

    member = db_session.get(Member, g.user_id)
    assert member is not None

    token = config.get("SLACK_BOT_TOKEN")
    slack_enabled = token is not None and token != ""

    has_slack_account = False
    if slack_enabled and member.email:
        try:
            slack_client = WebClient(token=token)
            slack_user_id = lookup_slack_user_by_email(slack_client, member.email)
            has_slack_account = slack_user_id is not None
        except Exception:
            # If we can't check, assume they don't have an account
            pass

    return {
        "slack_enabled": slack_enabled,
        "has_slack_account": has_slack_account,
        "task_delegation_enabled": is_task_delegation_enabled(g.user_id),
    }


@service.route("/current/task_delegation_enabled", method=POST, permission=USER)
def set_task_delegation_enabled(enabled: bool = Arg(bool)):
    """
    Enable or disable task delegation for the current member.
    This creates a new preference record.
    """
    pref = MemberPreference(
        member_id=g.user_id,
        question_type=MemberPreferenceQuestionType.TASK_DELEGATION_ENABLED,
        available_options="true,false",
        selected_options="true" if enabled else "false",
    )
    db_session.add(pref)
    db_session.commit()

    return {"enabled": enabled}


@service.route("/validate_phone_number", method=POST, permission=PUBLIC)
def validate_change_phone_number(id: int = Arg(int), validation_code=Arg(int)):
    return change_phone_validate(g.user_id, id, validation_code)


@service.route("/licenses", method=GET, permission=USER)
def get_licenses():
    return get_license_html_text()
