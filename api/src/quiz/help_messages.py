"""
Module for sending Slack help messages to members after they complete a quiz for the first time.

This module handles two scenarios:
1. Member completes a quiz and is currently at the space -> send message immediately
2. Member completed a quiz earlier and now opens a door -> send message on door open
"""

from datetime import datetime, timedelta
from logging import getLogger

from membership.models import Member
from multiaccessy.models import PhysicalAccessEntry
from redis_cache import redis_connection
from service.config import config
from service.db import db_session
from slack.util import format_member_mention_list, get_slack_client, lookup_slack_user_by_email, lookup_slack_users
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.models.blocks import Block, DividerBlock, MarkdownTextObject, SectionBlock
from sqlalchemy import select

from quiz.models import Quiz

logger = getLogger("quiz-help-messages")

# Duration for which a member is considered "at the space" after having opened a door.
DURATION_AT_SPACE_HEURISTIC = timedelta(minutes=90)

# Redis key prefix for tracking which quiz completion messages have been sent
QUIZ_COMPLETION_MESSAGE_SENT_PREFIX = "quiz_completion_message_sent"


def has_quiz_completion_message_been_sent(member_id: int, quiz_id: int) -> bool:
    """Check if we've already sent a completion message for this quiz to this member."""
    cache_key = f"{QUIZ_COMPLETION_MESSAGE_SENT_PREFIX}:{member_id}:{quiz_id}"
    return redis_connection.exists(cache_key) > 0


def mark_quiz_completion_message_sent(member_id: int, quiz_id: int) -> None:
    """Mark that we've sent a completion message for this quiz to this member."""
    cache_key = f"{QUIZ_COMPLETION_MESSAGE_SENT_PREFIX}:{member_id}:{quiz_id}"
    # Store indefinitely - we only want to send this message once ever
    redis_connection.set(cache_key, "1")


def is_member_at_space(member_id: int, now: datetime | None = None) -> bool:
    """Check if a member is currently at the makerspace based on recent door openings."""
    if now is None:
        now = datetime.now()

    recent_door_open = db_session.execute(
        select(PhysicalAccessEntry.id).where(
            PhysicalAccessEntry.member_id == member_id,
            PhysicalAccessEntry.created_at >= now - DURATION_AT_SPACE_HEURISTIC,
        )
    ).first()

    return recent_door_open is not None


def get_members_at_space_who_completed_quiz(quiz_id: int) -> list[Member]:
    """
    Get a list of members currently at the space who have completed the specified quiz.

    Args:
        quiz_id: The ID of the quiz to check

    Returns:
        List of Member objects who are at the space and have completed the quiz
    """
    now = datetime.now()

    # Get members who are currently at the space
    members_at_space = (
        db_session.execute(
            select(Member)
            .join(PhysicalAccessEntry, PhysicalAccessEntry.member_id == Member.member_id)
            .where(
                PhysicalAccessEntry.created_at >= now - DURATION_AT_SPACE_HEURISTIC,
                Member.deleted_at == None,
            )
            .distinct()
        )
        .scalars()
        .all()
    )

    # Filter to only those who have completed the quiz
    # We use calculate_max_pass_rate to check if they've ever completed it
    from quiz.views import calculate_max_pass_rate

    completed_members = []
    for member in members_at_space:
        _, ever_completed, _ = calculate_max_pass_rate(member.member_id, quiz_id)
        if ever_completed:
            completed_members.append(member)

    return completed_members


def send_quiz_completion_message(
    member: Member,
    quiz: Quiz,
    slack_members: list[str],
) -> bool:
    """
    Send a Slack message congratulating the member on completing a quiz,
    and letting them know about other members who can help.

    Args:
        member: The member who completed the quiz
        quiz: The quiz that was completed
        experienced_members: List of members at the space who have also done the quiz

    Returns:
        True if the message was sent successfully, False otherwise
    """
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        logger.warning("No SLACK_BOT_TOKEN configured; skipping Slack send")
        return False

    slack_client = WebClient(token=token)
    slack_user = lookup_slack_user_by_email(slack_client, member.email)
    if not slack_user:
        logger.info(f"Member {member.email} does not have a Slack account linked.")
        return False

    name = quiz.name
    if "Course" not in name and "Quiz" not in name:
        name += " Course"

    text = f"Congratulations {member.firstname}! :tada: I see you recently completed the *{name}*!\n\n"

    experienced_members_text = format_member_mention_list(slack_members)

    blocks: list[Block] = [
        DividerBlock(),
        SectionBlock(text=MarkdownTextObject(text=text)),
    ]

    if experienced_members_text:
        help_text = f"If you need help getting started, you can ask {experienced_members_text} who have also completed this course. They should be at the space right now."
        blocks.append(SectionBlock(text=MarkdownTextObject(text=help_text)))
    else:
        logger.info(
            f"No experienced members to help for member #{member.member_number} on quiz {quiz.id}. Trying again next time they open a door."
        )
        return False

    try:
        slack_client.chat_postMessage(
            channel=slack_user,
            text=text,
            blocks=blocks,
        )
        logger.info(f"Sent quiz completion message to member #{member.member_number} for quiz {quiz.id}")
        mark_quiz_completion_message_sent(member.member_id, quiz.id)
        return True
    except SlackApiError as e:
        logger.error(f"Failed to send Slack message to #{member.member_number}: {e.response['error']}")
        return False


def check_and_send_quiz_completion_message(member_id: int, quiz_id: int) -> bool:
    """
    Check if a quiz completion message should be sent and send it if appropriate.

    This should be called when:
    1. A member completes a quiz (answers all questions correctly)
    2. A member opens a door at the makerspace

    The message will only be sent if:
    - The member has completed the quiz
    - A message hasn't been sent before for this quiz/member combination
    - There are other members at the space who have also completed the quiz

    Args:
        member_id: The ID of the member to potentially send the message to
        quiz_id: The ID of the quiz to check

    Returns:
        True if a message was sent, False otherwise
    """
    # Check if we've already sent this message
    # We store this in redis, which is a bit ephemeral, but it's acceptable to potentially resend if we ever lose it
    # We only send it if the user completed the quiz within the last 2 months in any case.
    # TODO: We should store all slack messages in the database, to allow a proper check here.
    if has_quiz_completion_message_been_sent(member_id, quiz_id):
        return False

    # Check if the member has actually completed this quiz within the last 2 months
    from quiz.views import calculate_max_pass_rate

    _, ever_completed, completion_date = calculate_max_pass_rate(member_id, quiz_id)
    if not ever_completed:
        return False

    # Only send message if quiz was completed within the last 2 months
    if completion_date is None or completion_date < datetime.now() - timedelta(days=60):
        return False

    slack_client = get_slack_client()
    if not slack_client:
        return False

    # Check if member is at the space
    if not is_member_at_space(member_id):
        return False

    # Get other members at the space who have completed this quiz
    experienced_members = get_members_at_space_who_completed_quiz(quiz_id)[:20]
    slack_members = lookup_slack_users(
        get_slack_client(), [m for m in experienced_members if m.member_id != member_id]
    )[:3]

    # Only send if there are other members who can help
    if not slack_members:
        logger.info(
            f"No other members at space who have completed quiz {quiz_id}, not sending message to member {member_id}"
        )
        return False

    # Get member and quiz objects
    member = db_session.get(Member, member_id)
    quiz = db_session.get(Quiz, quiz_id)

    if not member or not quiz:
        logger.error(f"Could not find member {member_id} or quiz {quiz_id}")
        return False

    # Send the message
    if send_quiz_completion_message(member, quiz, slack_members):
        return True

    return False


def check_pending_quiz_completions_for_member(member_id: int) -> None:
    """
    Check if there are any quiz completions that haven't had a help message sent yet,
    and send them if appropriate.

    This should be called when a member opens a door at the makerspace.

    Args:
        member_id: The ID of the member who just opened a door
    """
    from quiz.views import member_quiz_statistics

    # Get all quizzes the member has completed
    stats = member_quiz_statistics(member_id)

    for stat in stats:
        if stat.ever_completed:
            quiz_id = stat.quiz["id"]
            check_and_send_quiz_completion_message(member_id, quiz_id)
