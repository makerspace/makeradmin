import serde
from change_phone_request import change_phone_request, change_phone_validate
from flask import g, request
from membership.member_auth import get_member_permissions
from membership.membership import get_access_summary, get_membership_summary
from membership.models import Member, SlackEmailOverride
from membership.views import member_entity
from multiaccess.memberbooth import get_member_labels
from quiz.views import member_quiz_statistics
from service.api_definition import DELETE, GET, MESSAGE_SEND, POST, PUBLIC, USER, Arg, natural1, non_empty_str
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
    from slack.util import get_slack_email_for_member, lookup_slack_user_by_email
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
            email = get_slack_email_for_member(member)
            slack_user_id = lookup_slack_user_by_email(slack_client, email)
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


@service.route("/current/slack_email", method=GET, permission=USER)
def get_slack_email():
    """Get the current member's Slack email override, if any, plus their Slack account info."""
    from service.config import config
    from slack.util import lookup_slack_user_by_email
    from slack_sdk import WebClient

    member = db_session.get(Member, g.user_id)
    assert member is not None

    # Get override if it exists (single query)
    override = db_session.execute(
        select(SlackEmailOverride).where(SlackEmailOverride.member_id == g.user_id)
    ).scalar_one_or_none()

    slack_override_email = override.slack_email if override else None
    effective_slack_email = slack_override_email if slack_override_email else member.email

    # Try to get Slack username if configured
    token = config.get("SLACK_BOT_TOKEN")
    slack_username = None
    if token:
        try:
            slack_client = WebClient(token=token)
            slack_user_id = lookup_slack_user_by_email(slack_client, effective_slack_email)
            if slack_user_id:
                user_info = slack_client.users_info(user=slack_user_id)
                slack_username = user_info["user"]["profile"].get("real_name") or user_info["user"]["name"]
        except Exception:
            # If we can't get the username, just return None
            pass

    return {
        "slack_override_email": slack_override_email,
        "effective_slack_email": effective_slack_email,
        "slack_username": slack_username,
    }


@service.route("/current/slack_email", method=POST, permission=USER)
def set_slack_email(slack_email: str = Arg(non_empty_str)):
    """Set or update the Slack email override for the current member."""
    from service.error import BadRequest
    from slack.util import get_slack_client, lookup_slack_user_by_email
    from slack.verification import store_verification
    from slack_sdk.models.blocks import ActionsBlock, ButtonElement, SectionBlock

    # Validate email format (basic check)
    if "@" not in slack_email or "." not in slack_email:
        raise BadRequest("Invalid email format")

    # Look up Slack user by email
    slack_client = get_slack_client()
    if not slack_client:
        raise BadRequest("Slack integration not configured")

    slack_user_id = lookup_slack_user_by_email(slack_client, slack_email)
    if not slack_user_id:
        raise BadRequest("No Slack account found with that email address. Please check the email or join Slack first.")

    # Store verification in Redis
    store_verification(g.user_id, slack_email, slack_user_id)

    # Get current member for display
    member = db_session.get(Member, g.user_id)
    member_name = f"{member.firstname} {member.lastname}" if member else "Member"

    # Send Slack DM with confirmation buttons
    try:
        slack_client.chat_postMessage(
            channel=slack_user_id,
            text=f"Confirm Slack email linking for {slack_email}",
            blocks=[
                SectionBlock(
                    text=f"*Confirm Slack Email Linking*\n\n"
                    f"You (_{member_name}_) are about to link your MakerAdmin account to this Slack account using the email address *{slack_email}*.\n\n"
                    f"This will allow the system to send you notifications and task assignments via Slack DM.\n\n"
                    f"Please confirm this is correct by clicking the button below. This verification will expire in 15 minutes."
                ),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text="Confirm",
                            action_id="slack_email_confirm",
                            style="primary",
                            value="confirm",
                        ),
                        ButtonElement(
                            text="Cancel",
                            action_id="slack_email_cancel",
                            value="cancel",
                        ),
                    ]
                ),
            ],
        )
    except Exception as e:
        import logging

        logger = logging.getLogger("makeradmin")
        logger.error(f"Failed to send Slack verification message: {e}")
        raise BadRequest("Failed to send verification message to Slack")

    return {"status": "verification_sent", "slack_email": slack_email}


@service.route("/current/slack_email", method=DELETE, permission=USER)
def delete_slack_email():
    """Remove the Slack email override for the current member."""
    override = db_session.execute(
        select(SlackEmailOverride).where(SlackEmailOverride.member_id == g.user_id)
    ).scalar_one_or_none()

    if override:
        db_session.delete(override)
        db_session.commit()

    return {"deleted": override is not None}


@service.route("/validate_phone_number", method=POST, permission=PUBLIC)
def validate_change_phone_number(id: int = Arg(int), validation_code=Arg(int)):
    return change_phone_validate(g.user_id, id, validation_code)


@service.route("/licenses", method=GET, permission=USER)
def get_licenses():
    return get_license_html_text()
