"""
Module for sending Slack help messages to members after they complete a quiz for the first time.

This module handles two scenarios:
1. Member completes a quiz and is currently at the space -> send message immediately
2. Member completed a quiz earlier and now opens a door -> send message on door open
"""

import json
from datetime import datetime, timedelta
from logging import getLogger

from membership.models import Member
from messages.message import send_message
from messages.models import Message, MessageTemplate
from multiaccessy.models import PhysicalAccessEntry
from service.db import db_session
from slack.util import format_member_mention_list, get_slack_client, lookup_slack_users
from slack_sdk.models.blocks import DividerBlock, MarkdownTextObject, SectionBlock
from sqlalchemy import select

from quiz.models import Quiz

logger = getLogger("quiz-help-messages")

# Duration for which a member is considered "at the space" after having opened a door.
DURATION_AT_SPACE_HEURISTIC = timedelta(minutes=90)


def has_quiz_completion_message_been_sent(member_id: int, quiz_id: int) -> bool:
    """Check if we've already sent a completion message for this quiz to this member."""
    # Check the Message table for an existing QUIZ_COMPLETION message
    # with the quiz_id stored in associated_id
    existing_message = db_session.execute(
        select(Message.id).where(
            Message.member_id == member_id,
            Message.template == MessageTemplate.QUIZ_COMPLETION.value,
            Message.associated_id == quiz_id,
        )
    ).first()
    return existing_message is not None


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
    Queue a Slack message congratulating the member on completing a quiz,
    and letting them know about other members who can help.

    Args:
        member: The member who completed the quiz
        quiz: The quiz that was completed
        slack_members: List of Slack user IDs for members at the space who have also done the quiz

    Returns:
        True if the message was queued successfully, False otherwise
    """
    experienced_members_text = format_member_mention_list(slack_members)

    if not experienced_members_text:
        logger.info(
            f"No experienced members to help for member #{member.member_number} on quiz {quiz.id}. Trying again next time they open a door."
        )
        return False

    # Format the message as Slack blocks
    quiz_name = quiz.name
    if "Course" not in quiz_name and "Quiz" not in quiz_name:
        quiz_name += " Course"

    congratulations_text = (
        f"Congratulations {member.firstname}! :tada: I see you recently completed the *{quiz_name}*!\n\n"
    )
    help_text = f"If you need help getting started, you can ask {experienced_members_text} who have also completed this course. They should be at the space right now."

    blocks = [
        DividerBlock(),
        SectionBlock(text=MarkdownTextObject(text=congratulations_text)),
        SectionBlock(text=MarkdownTextObject(text=help_text)),
    ]

    # Serialize blocks to JSON for database storage
    body = json.dumps([block.to_dict() for block in blocks])

    # Subject is used as fallback text for notifications
    subject = f"Congratulations on completing {quiz.name}!"

    # Queue the message in the database
    # The dispatch_slack.py service will pick it up and send it
    send_message(
        template=MessageTemplate.QUIZ_COMPLETION,
        member=member,
        db_session=db_session,
        recipient=member.email,  # Slack dispatcher will look up user by email
        recipient_type="slack",
        associated_id=quiz.id,  # Store quiz_id for tracking
        subject=subject,
        body=body,
    )

    logger.info(f"Queued quiz completion message to member #{member.member_number} for quiz {quiz.id}")
    return True


def check_and_send_quiz_completion_message(member_id: int, quiz_id: int) -> bool:
    """
    Check if a quiz completion message should be sent and send it if appropriate.

    This should be called when:
    1. A member completes a quiz (answers all questions correctly)
    2. A member opens a door at the makerspace

    The message will only be sent if:
    - The member has completed the quiz
    - A message hasn't been sent before for this quiz/member combination (tracked in database)
    - There are other members at the space who have also completed the quiz
    - The quiz has send_help_notifications enabled
    - The quiz was completed within the last 2 months

    Args:
        member_id: The ID of the member to potentially send the message to
        quiz_id: The ID of the quiz to check

    Returns:
        True if a message was sent, False otherwise
    """
    # Check if we've already sent this message by looking in the Message table
    if has_quiz_completion_message_been_sent(member_id, quiz_id):
        return False

    # Check if the quiz has help notifications enabled
    quiz = db_session.get(Quiz, quiz_id)
    if not quiz:
        logger.error(f"Could not find quiz {quiz_id}")
        return False

    if not quiz.send_help_notifications:
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

    # Get member object
    member = db_session.get(Member, member_id)

    if not member:
        logger.error(f"Could not find member {member_id}")
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
