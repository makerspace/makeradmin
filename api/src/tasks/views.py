import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import getLogger
from typing import Optional, cast, get_args

from flask import request
from membership.models import Member
from serde import from_dict, serde
from serde.json import from_json, to_json
from service.api_definition import GET, MEMBER_VIEW, POST, PUBLIC
from service.db import db_session
from service.error import BadRequest, NotFound, UnprocessableEntity
from slack.types import SlackInteraction
from slack.util import get_slack_client, member_from_slack_user_id
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.models.blocks import (
    ActionsBlock,
    Block,
    ButtonElement,
    ImageBlock,
    MarkdownTextObject,
    Option,
    PlainTextObject,
    SectionBlock,
    StaticSelectElement,
)
from sqlalchemy import select
from trello import trello

from tasks import service
from tasks.delegate import (
    DOOR_REQUIREMENT_NAMES,
    TASK_LOG_CHANNEL,
    CardCompletionInfo,
    CardRequirements,
    MemberTaskInfo,
    SlackInteraction,
    TaskContext,
    clear_pending_question,
    delegate_task_for_member,
    get_all_room_labels,
    member_recently_received_task,
    task_score,
    task_score_base,
    visit_events_by_member_id,
)
from tasks.models import MemberPreference, MemberPreferenceQuestionType, TaskDelegationLog, TaskDelegationLogLabel

logger = getLogger("task-delegator")


@dataclass
class TaskLogEntry:
    """A single task log entry for display in the admin UI."""

    id: int
    card_id: str
    card_name: str
    card_url: str
    action: str
    created_at: str
    labels: list[str]


@dataclass
class MemberTaskInfoResponse:
    """Response for the member task info endpoint."""

    task_logs: list[TaskLogEntry]
    preferred_rooms: Optional[list[str]]
    self_reported_skill_level: Optional[str]
    completed_tasks_by_label: dict[str, int]
    time_at_space_since_last_task_hours: float
    total_completed_tasks: int


@service.route("/member/<int:member_id>/task_info", method=GET, permission=MEMBER_VIEW)
def get_member_task_info(member_id: int) -> dict:
    """Get task delegation info for a member."""
    now = datetime.now()
    member_info = MemberTaskInfo.from_member(member_id, now)

    # Get all task logs for this member, ordered by date descending
    logs = (
        db_session.execute(
            select(TaskDelegationLog)
            .where(TaskDelegationLog.member_id == member_id)
            .order_by(TaskDelegationLog.created_at.desc())
        )
        .scalars()
        .all()
    )

    task_logs: list[dict] = []
    for log in logs:
        # Get labels for this log entry
        labels = (
            db_session.execute(select(TaskDelegationLogLabel.label).where(TaskDelegationLogLabel.log_id == log.id))
            .scalars()
            .all()
        )

        task_logs.append(
            {
                "id": log.id,
                "card_id": log.card_id,
                "card_name": log.card_name,
                "card_url": f"https://trello.com/c/{log.card_id}",
                "action": log.action,
                "created_at": log.created_at.isoformat(),
                "labels": list(labels),
            }
        )

    # Sort completed_tasks_by_label by label name
    sorted_completed_by_label = dict(sorted(member_info.completed_tasks_by_label.items()))

    return {
        "task_logs": task_logs,
        "preferred_rooms": sorted(member_info.preferred_rooms) if member_info.preferred_rooms else None,
        "self_reported_skill_level": member_info.self_reported_skill_level,
        "completed_tasks_by_label": sorted_completed_by_label,
        "time_at_space_since_last_task_hours": member_info.time_at_space_since_last_task_completed.total_seconds()
        / 3600,
        "total_completed_tasks": member_info.total_completed_tasks,
    }


@service.route("/statistics", method=GET, permission=MEMBER_VIEW)
def get_global_task_statistics() -> dict:
    """Get global task delegation statistics.

    If a member_id query parameter is provided, the score will be calculated
    for that specific member using the full task_score function (ignoring door requirements).
    Otherwise, the base score is used.
    """
    member_id = request.args.get("member_id", type=int)

    # Get all task logs, ordered by date descending, limited to recent entries
    logs = (
        db_session.execute(select(TaskDelegationLog).order_by(TaskDelegationLog.created_at.desc()).limit(500))
        .scalars()
        .all()
    )

    # Get cached cards from Trello (used for both task logs and card info)
    cards: list[trello.TrelloCard] = []
    try:
        cards = trello.cached_cards(trello.SOURCE_LIST_NAME)
    except Exception as e:
        logger.warning(f"Failed to fetch Trello cards: {e}")

    # Build a lookup dict for cards by id
    cards_by_id = {card.id: card for card in cards}

    task_logs: list[dict] = []
    for log in logs:
        # Get labels from Trello card if it exists, otherwise fall back to database
        card = cards_by_id.get(log.card_id)
        if card:
            labels = [label.name for label in card.labels]
        else:
            # Card doesn't exist in Trello (maybe deleted), fall back to database
            labels = list(
                db_session.execute(select(TaskDelegationLogLabel.label).where(TaskDelegationLogLabel.log_id == log.id))
                .scalars()
                .all()
            )

        # Get member name if available
        member_name = None
        if log.member_id:
            member = db_session.get(Member, log.member_id)
            if member:
                member_name = f"{member.firstname} {member.lastname}"

        task_logs.append(
            {
                "id": log.id,
                "card_id": log.card_id,
                "card_name": log.card_name,
                "card_url": f"https://trello.com/c/{log.card_id}",
                "action": log.action,
                "created_at": log.created_at.isoformat(),
                "labels": labels,
                "member_id": log.member_id,
                "member_name": member_name,
            }
        )

    # Prepare member context if member_id is provided
    now = datetime.now()
    member_ctx = None
    reference_task_assignment_contexts: list[TaskContext] = []

    if member_id is not None:
        member_ctx = TaskContext.from_member(member_id, now)

        # Build reference contexts for scoring (same as in select_card_for_member)
        visits = visit_events_by_member_id(now - timedelta(days=30), now)
        ASSIGN_DELAY = timedelta(minutes=3)
        reference_task_assignment_contexts = [
            TaskContext.from_cache(m, visit_time + ASSIGN_DELAY)
            for m, visit_times in visits.items()
            for (visit_time, _) in visit_times
        ]

    # Get card completion info for all cards from Trello
    cards_info: list[dict] = []
    for card in cards:
        completion_info = CardCompletionInfo.from_card(card)
        requirements = CardRequirements.from_card(card)

        # Calculate the score for this task
        if member_ctx is not None:
            # Use full task_score for member-specific scoring, ignoring door requirements
            score_result = task_score(
                requirements,
                completion_info,
                member_ctx,
                reference_task_assignment_contexts,
                ignore_reasons=DOOR_REQUIREMENT_NAMES,
                all_cards=cards,
            )
            final_score = round(score_result.score, 2)
            cannot_be_assigned_reason = (
                score_result.cannot_be_assigned_reason.reason if score_result.cannot_be_assigned_reason else None
            )
        else:
            # Use base score when no member is specified
            score_result = task_score_base(requirements, completion_info, now)
            final_score = round(score_result.score, 2)
            cannot_be_assigned_reason = None

        # Calculate overdue days
        overdue_days: float | None = None
        if requirements.repeat_interval is not None:
            last_time = completion_info.last_completed or completion_info.first_available_at
            elapsed = now - last_time
            overdue_seconds = elapsed.total_seconds() - requirements.repeat_interval.total_seconds()
            if overdue_seconds > 0:
                overdue_days = overdue_seconds / 86400  # seconds per day

        cards_info.append(
            {
                "card_id": completion_info.card_id,
                "card_name": completion_info.card_name,
                "card_url": f"https://trello.com/c/{completion_info.card_id}",
                "first_available_at": completion_info.first_available_at.isoformat(),
                "assigned_count": completion_info.assigned_count,
                "completed_count": completion_info.completed_count,
                "last_completed": completion_info.last_completed.isoformat()
                if completion_info.last_completed
                else None,
                "last_completer_id": completion_info.last_completer.member_id
                if completion_info.last_completer
                else None,
                "last_completer_name": f"{completion_info.last_completer.firstname} {completion_info.last_completer.lastname}"
                if completion_info.last_completer
                else None,
                "score": final_score,
                "overdue_days": overdue_days,
                "cannot_be_assigned_reason": cannot_be_assigned_reason,
                "score_calculation": [
                    {
                        "operation": op.operation.value,
                        "value": op.value,
                        "description": op.description,
                    }
                    for op in score_result.score_calculation
                ],
            }
        )

    return {
        "task_logs": task_logs,
        "cards": cards_info,
        "member_id": member_id,
    }


@service.route("/statistics/member_preferences", method=GET, permission=MEMBER_VIEW)
def get_member_preference_statistics() -> dict:
    """Get statistics about member preferences/survey responses."""
    from sqlalchemy import distinct, func

    stats_by_question_type: dict[str, dict] = {}

    for question_type in MemberPreferenceQuestionType:
        # Get the most recent preference for each member for this question type
        # Using a subquery to get the latest preference per member
        latest_pref_subquery = (
            db_session.query(
                MemberPreference.member_id,
                func.max(MemberPreference.id).label("max_id"),
            )
            .filter(MemberPreference.question_type == question_type)
            .group_by(MemberPreference.member_id)
            .subquery()
        )

        # Get the actual preferences using the subquery
        latest_prefs = (
            db_session.execute(
                select(MemberPreference)
                .join(
                    latest_pref_subquery,
                    (MemberPreference.member_id == latest_pref_subquery.c.member_id)
                    & (MemberPreference.id == latest_pref_subquery.c.max_id),
                )
                .where(MemberPreference.question_type == question_type)
            )
            .scalars()
            .all()
        )

        # Count responses by option
        option_counts: dict[str, int] = {}
        total_respondents = len(latest_prefs)

        for pref in latest_prefs:
            # Handle comma-separated multi-select options
            selected = pref.selected_options.split(",") if pref.selected_options else []
            for option in selected:
                option = option.strip()
                if option:
                    option_counts[option] = option_counts.get(option, 0) + 1

        # Calculate how many members haven't answered this question
        # Get total number of active (non-deleted) members
        total_members = db_session.execute(
            select(func.count(Member.member_id)).where(Member.deleted_at.is_(None))
        ).scalar()
        unanswered_count = total_members - total_respondents

        # Sort options by count descending
        sorted_options = sorted(option_counts.items(), key=lambda x: (-x[1], x[0]))

        stats_by_question_type[question_type.value] = {
            "question_type": question_type.value,
            "total_respondents": total_respondents,
            "unanswered": unanswered_count,
            "options": [{"option": opt, "count": count} for opt, count in sorted_options],
        }

    return {"preference_statistics": stats_by_question_type}


@service.route("/slack/events", method=POST, permission=PUBLIC)  # PUBLIC because Slack posts here
def slack_events() -> dict:
    """
    Slack Events API endpoint.
    Handles URL verification and message events.
    """
    data = request.get_json()
    if not data:
        raise BadRequest("Missing JSON body")

    # Handle URL verification challenge (Slack sends this when setting up the endpoint)
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}

    # Handle events
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_type = event.get("type")

        # Handle message events
        if event_type == "message":
            # Ignore bot messages to avoid loops
            if event.get("bot_id"):
                return {"ok": True}

            # Check if message contains @theSpace or @thespace
            text = event.get("text", "").lower()
            if (
                "@thespace" in text
                or "someone at the space" in text
                or "anyone at makerspace now" in text
                or "anyone at the makerspace right now" in text
            ):
                handle_thespace_mention(event)

        return {"ok": True}

    return {"ok": True}


def get_all_channel_members(slack_client: WebClient, channel_id: str) -> set[str]:
    """
    Get all member IDs in a Slack channel, handling pagination.

    Args:
        slack_client: The Slack WebClient instance
        channel_id: The channel ID to fetch members from

    Returns:
        A set of member IDs in the channel

    Raises:
        SlackApiError: If the API call fails
    """
    channel_member_ids = set()
    cursor = None

    while True:
        response = slack_client.conversations_members(
            channel=channel_id,
            limit=200,
            cursor=cursor
        )
        channel_member_ids.update(response.get("members", []))

        # Check if there are more results to fetch
        next_cursor = response.get("response_metadata", {}).get("next_cursor")
        if not next_cursor:
            break
        cursor = next_cursor

    return channel_member_ids


def handle_thespace_mention(event: dict) -> None:
    """Handle when someone mentions @theSpace in a message."""
    from tasks.delegate import DURATION_AT_SPACE_HEURISTIC

    slack_client = get_slack_client()
    if not slack_client:
        logger.error("Slack client not available")
        return

    channel_id = event.get("channel")
    if not channel_id:
        return

    try:
        # Get members currently at the space
        from slack.util import format_member_mention_list, get_members_currently_at_space, lookup_slack_user_by_email

        members_at_space = get_members_currently_at_space(DURATION_AT_SPACE_HEURISTIC)

        if not members_at_space:
            slack_client.chat_postMessage(
                channel=channel_id,
                text="No one is currently at the space (or at least, no one has entered recently).",
                thread_ts=event.get("ts"),  # Reply in thread if it's a thread message
            )
            return

        # Get channel members to filter the list
        try:
            channel_member_ids = get_all_channel_members(slack_client, channel_id)
        except SlackApiError as e:
            # If we can't get channel members (e.g., DM or private channel), skip filtering
            logger.warning(f"Could not get channel members for {channel_id}: {e.response['error']}")
            channel_member_ids = None

        # Look up Slack user IDs for all members
        slack_user_ids = []
        slack_user_ids_not_in_channel = []
        for member in members_at_space:
            slack_user_id = lookup_slack_user_by_email(slack_client, member.email)
            if slack_user_id:
                # Filter to only members in this channel (if we have that info)
                if channel_member_ids is None or slack_user_id in channel_member_ids:
                    slack_user_ids.append(slack_user_id)
                else:
                    slack_user_ids_not_in_channel.append(slack_user_id)

        if not slack_user_ids and not slack_user_ids_not_in_channel:
            slack_client.chat_postMessage(
                channel=channel_id,
                text=f"{len(members_at_space)} member(s) at the space, but couldn't find their Slack accounts.",
                thread_ts=event.get("ts"),
            )
            return

        # Format the message nicely using the helper function
        if slack_user_ids:
            mentions = format_member_mention_list(slack_user_ids)
            if len(slack_user_ids) == 1:
                message = f"Here's who is at the space right now: {mentions}"
            else:
                message = f"Here's everyone who is at the space right now: {mentions}"

            # Add note about additional members not in this channel
            if slack_user_ids_not_in_channel:
                count = len(slack_user_ids_not_in_channel)
                if count == 1:
                    message += " (and 1 other member who is not in this channel)"
                else:
                    message += f" (and {count} other members who are not in this channel)"
        else:
            # Everyone at the space is not in this channel
            count = len(slack_user_ids_not_in_channel)
            if count == 1:
                message = "1 member is at the space, but they are not in this channel."
            else:
                message = f"{count} members are at the space, but they are not in this channel."

        slack_client.chat_postMessage(
            channel=channel_id,
            text=message,
            thread_ts=event.get("ts"),  # Reply in thread if it's a thread message
        )

        logger.info(
            f"Responded to @theSpace mention in channel {channel_id}: "
            f"{len(slack_user_ids)} in channel, {len(slack_user_ids_not_in_channel)} not in channel"
        )

    except SlackApiError as e:
        logger.error(f"Failed to respond to @theSpace mention: {e.response['error']}")
    except Exception as e:
        logger.exception(f"Error handling @theSpace mention: {e}")


@service.route("/slack/interaction", method=POST, permission=PUBLIC)  # PUBLIC because Slack posts here
def slack_interaction() -> dict:
    """
    Slack interaction endpoint.
    Expects 'payload' form param with JSON body from Slack.
    """
    json = request.form.get("payload")
    if not json:
        raise BadRequest("Missing JSON payload")
    logger.info(f"Received Slack interaction payload:\n{json}")
    payload = from_json(SlackInteraction, json)

    if not payload.actions:
        raise BadRequest("No actions in payload")

    action = payload.actions[0]

    if action.action_id == "room_preference_submit":
        return slack_handle_room_preference_submission(payload)
    elif action.action_id.startswith("skill_level_submit"):
        return slack_handle_skill_level_submission(payload)
    elif action.action_id == "room_preference_checkboxes" or action.action_id == "room_preference_select":
        # Ignore intermediate actions from the room preference selection
        # This happens when the user selects/deselects options but hasn't submitted yet
        return {"message": "Intermediate action ignored"}
    elif action.action_id == "new_task":
        return slack_handle_new_task_request(payload)
    else:
        return slack_handle_task_feedback(payload)


def slack_handle_new_task_request(payload: SlackInteraction) -> dict:
    """Handle when a member requests a new task."""
    slack_client = get_slack_client()
    member = member_from_slack_user_id(slack_client, payload.user.id)

    if not member:
        raise UnprocessableEntity("Member not found")

    delegate_task_for_member(member.member_id, slack_interaction=payload, force=True)

    return {"message": "New task assigned"}


def slack_handle_room_preference_submission(payload: SlackInteraction) -> dict:
    """Handle when a member submits their room preferences."""
    slack_client = get_slack_client()
    member = member_from_slack_user_id(slack_client, payload.user.id)

    if not member:
        raise UnprocessableEntity("Member not found")

    # Check if the message is too old (>1 month)
    # Slack message timestamp is in format like "1234567890.123456"
    message_timestamp = float(payload.message.ts)
    message_datetime = datetime.fromtimestamp(message_timestamp)
    now = datetime.now()

    if now - message_datetime > timedelta(days=30):
        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=":information_source: Thanks. But this question was asked too long ago and has expired. If we need this information, we'll ask again.",
        )
        logger.info(
            f"Member {member.member_id} responded to a room preference question that was too old (from {message_datetime})"
        )
        return {"message": "Question too old"}

    # Extract selected rooms from the state values
    # Slack sends checkbox selections in state.values
    selected_rooms = []
    if payload.state:
        state_values = payload.state.values
        # Look for the room_preferences block
        if "room_preferences" in state_values:
            room_prefs = state_values["room_preferences"]
            # Look for the checkbox action
            if "room_preference_checkboxes" in room_prefs:
                checkbox_data = room_prefs["room_preference_checkboxes"]
                # Extract selected options
                if checkbox_data.selected_options:
                    selected_rooms = [opt.value for opt in checkbox_data.selected_options]

    if not selected_rooms:
        slack_client.chat_postMessage(
            channel=payload.channel.id,
            text="Please select at least one room before submitting.",
        )
        return {"message": "No rooms selected"}

    # Get all available rooms from cards
    cards = trello.cached_cards(trello.SOURCE_LIST_NAME)

    available_rooms = get_all_room_labels(cards)
    # Validate selected rooms
    for room in selected_rooms:
        if room not in available_rooms:
            raise BadRequest(f"Invalid room selected: {room}")

    # Save preference
    new_pref = MemberPreference(
        member_id=member.member_id,
        question_type=MemberPreferenceQuestionType.ROOM_PREFERENCE,
        available_options=",".join(available_rooms),
        selected_options=",".join(selected_rooms),
    )
    db_session.add(new_pref)

    db_session.commit()

    # Clear the pending question flag
    clear_pending_question(member.member_id)

    # Thank the member and assign them a task.
    # If they have recently received a task or haven't visited in the last 3 hours, just thank them.
    ctx = TaskContext.from_member(member.member_id, datetime.now())
    if (
        member_recently_received_task(ctx)
        or len(visit_events_by_member_id(now - timedelta(hours=3), now, member.member_id)) == 0
    ):
        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=f":white_check_mark: Thanks! You've selected: {', '.join(selected_rooms)}. We'll prioritize tasks in these rooms for you.",
            blocks=[
                SectionBlock(
                    text=MarkdownTextObject(
                        text=f":white_check_mark: Thanks! You've selected: {', '.join(selected_rooms)}. We'll prioritize tasks in these rooms for you."
                    )
                ),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="↻ Find me a task now", emoji=True),
                            action_id="new_task",
                            value="new_task",
                        ),
                    ]
                ),
            ],
        )
    else:
        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=f":white_check_mark: Thanks! You've selected: {', '.join(selected_rooms)}. We'll prioritize tasks in these rooms for you. Let's find you a task now...",
        )

        # Now assign them a task
        delegate_task_for_member(member.member_id, slack_interaction=None, force=True)

    return {"message": "Preferences saved and task assigned"}


def slack_handle_skill_level_submission(payload: SlackInteraction) -> dict:
    """Handle when a member submits their skill level."""
    slack_client = get_slack_client()
    member = member_from_slack_user_id(slack_client, payload.user.id)

    if not member:
        raise UnprocessableEntity("Member not found")

    # Check if the message is too old (>1 month)
    # Slack message timestamp is in format like "1234567890.123456"
    message_timestamp = float(payload.message.ts)
    message_datetime = datetime.fromtimestamp(message_timestamp)
    now = datetime.now()

    if now - message_datetime > timedelta(days=30):
        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=":information_source: Thanks. But this question was asked too long ago and has expired. If we need this information, we'll ask again.",
        )
        logger.info(
            f"Member {member.member_id} responded to a skill level question that was too old (from {message_datetime})"
        )
        return {"message": "Question too old"}

    # Extract selected skill level from button action
    action = payload.actions[0]
    selected_skill_level = action.value

    if not selected_skill_level:
        slack_client.chat_postMessage(
            channel=payload.channel.id,
            text="Please select your skill level.",
        )
        return {"message": "No skill level selected"}

    # Validate selected skill level
    valid_skill_levels = ["beginner", "intermediate", "advanced", "expert"]
    if selected_skill_level not in valid_skill_levels:
        raise BadRequest(f"Invalid skill level selected: {selected_skill_level}")

    # Save preference
    new_pref = MemberPreference(
        member_id=member.member_id,
        question_type=MemberPreferenceQuestionType.SKILL_LEVEL,
        available_options=",".join(valid_skill_levels),
        selected_options=selected_skill_level,
    )
    db_session.add(new_pref)

    db_session.commit()

    # Clear the pending question flag
    clear_pending_question(member.member_id)

    # Post in the global channel that the member has selected a skill level
    if TASK_LOG_CHANNEL is not None:
        slack_client.chat_postMessage(
            channel=TASK_LOG_CHANNEL,
            text=f"Member #{member.member_number} {member.firstname} {member.lastname} selected skill level: {selected_skill_level}",
        )

    # Thank the member and assign them a task.
    # If they have recently received a task or haven't visited in the last 3 hours, just thank them.
    ctx = TaskContext.from_member(member.member_id, datetime.now())
    if (
        member_recently_received_task(ctx)
        or len(visit_events_by_member_id(now - timedelta(hours=3), now, member.member_id)) == 0
    ):
        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=f":white_check_mark: Thanks! You've selected skill level: {selected_skill_level}. We'll assign tasks that match your experience.",
            blocks=[
                SectionBlock(
                    text=MarkdownTextObject(
                        text=f":white_check_mark: Thanks! You've selected skill level: {selected_skill_level}. We'll start by assigning tasks that match your experience level. But you'll be given more advanced tasks as you gain experience."
                    )
                ),
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="↻ Find me a task now", emoji=True),
                            action_id="new_task",
                            value="new_task",
                        ),
                    ]
                ),
            ],
        )
    else:
        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=f":white_check_mark: Thanks! You've selected skill level: {selected_skill_level}. We'll start by assigning tasks that match your experience level. But you'll be given more advanced tasks as you gain experience. Let's find you a task now...",
        )

        # Now assign them a task
        delegate_task_for_member(member.member_id, slack_interaction=None, force=True)

    return {"message": "Skill level saved and task assigned"}


def slack_handle_task_feedback(payload: SlackInteraction, ignore_reasons: list[str] = []) -> dict:
    action = payload.actions[0]
    action_type = action.action_id
    sub_action = action.selected_option.value if action.selected_option is not None else action.value

    log = db_session.execute(
        select(TaskDelegationLog)
        .where(
            TaskDelegationLog.slack_channel_id == payload.channel.id,
            TaskDelegationLog.slack_message_ts == payload.message.ts,
        )
        .order_by(TaskDelegationLog.id.desc())
        .limit(1)  # If the task was re-rolled multiple times, get the latest one
    ).scalar_one_or_none()
    if not log:
        raise NotFound("No such task has been delegated")

    member = db_session.get(Member, log.member_id)
    assert member is not None

    slack_client = get_slack_client()
    now = datetime.now()

    try:
        card = trello.get_card(log.card_id)
    except Exception as e:
        logger.error(f"Failed to fetch Trello card {log.card_id}: {e}")
        raise BadRequest("Trello card not found")

    if action_type == "task_feedback_done":
        if sub_action != "done":
            raise BadRequest(f"Invalid sub-action '{sub_action}'")

        if log.action == "completed":
            return {"message": "Task already marked done"}

        # Update log and move trello card
        log.action = "completed"

        requirements = CardRequirements.from_card(card)
        ctx = TaskContext.from_member(member.member_id, now)

        try:
            if not requirements.infinitely_repeatable and requirements.repeat_interval is None:
                trello.move_card_to_done(log.card_id)

            trello.add_comment_to_card(
                log.card_id, f"Marked completed by member #{member.member_number} {member.firstname} {member.lastname}"
            )
        except Exception as e:
            logger.error(f"Failed to update Trello card {log.card_id}: {e}")

        db_session.add(log)
        db_session.commit()

        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=":white_check_mark: Thank you! The task has been marked as completed. :star2:",
            blocks=[
                SectionBlock(
                    text=MarkdownTextObject(
                        text=f":white_check_mark: Thank you! The task *{log.card_name}* has been marked as completed. :star2:"
                    )
                ),
                *[
                    SectionBlock(text=MarkdownTextObject(text=text))
                    for text in requirements.completion_messages_for_context(ctx)
                ],
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="↻ I can do something else too", emoji=True),
                            action_id="task_feedback_new_task",
                            value="new_task",
                        ),
                    ]
                ),
            ],
        )

        if TASK_LOG_CHANNEL is not None:
            slack_client.chat_postMessage(
                channel=TASK_LOG_CHANNEL,
                text=f":white_check_mark: Member #{member.member_number} {member.firstname} {member.lastname} completed the task: <https://trello.com/c/{card.id}|{log.card_name}>",
            )
        return {"message": "Thanks — marked done"}
    elif action_type == "task_feedback_not_done":
        if sub_action not in get_args(TaskDelegationLog.ACTION_TYPE):
            raise BadRequest(f"Invalid sub-action '{sub_action}'")

        if log.action != "assigned":
            return {"message": "Task already completed or marked as not done"}

        log.action = cast(TaskDelegationLog.ACTION_TYPE, sub_action)
        db_session.add(log)
        db_session.commit()

        if sub_action == "already_completed_by_someone_else":
            trello.add_comment_to_card(
                log.card_id,
                f"Member #{member.member_number} {member.firstname} {member.lastname} reported the task was already completed by someone else",
            )

            if TASK_LOG_CHANNEL is not None:
                slack_client.chat_postMessage(
                    channel=TASK_LOG_CHANNEL,
                    text=f"Member #{member.member_number} {member.firstname} {member.lastname} reported the task <https://trello.com/c/{card.id}|{log.card_name}> was already completed by someone else",
                )

            slack_client.chat_update(
                channel=payload.channel.id,
                ts=payload.message.ts,
                blocks=[
                    SectionBlock(
                        text=MarkdownTextObject(
                            text=f":ballot_box_with_check: Great! Thanks for letting us know that the task *{log.card_name}* was already done by someone else."
                        )
                    ),
                    ActionsBlock(
                        elements=[
                            ButtonElement(
                                text=PlainTextObject(text="↻ I can do something else", emoji=True),
                                action_id="new_task",
                                value="new_task",
                            ),
                        ]
                    ),
                ],
            )

            return {"message": "Marked as completed by someone else"}
        else:
            trello.add_comment_to_card(
                log.card_id,
                f"Member #{member.member_number} {member.firstname} {member.lastname} reported they couldn't do the task: {sub_action}",
            )

            slack_client.chat_update(
                channel=payload.channel.id,
                ts=payload.message.ts,
                text=f":thumbsup: Can't do the task *{log.card_name}* right now? No worries, thanks for letting us know. We'll give you something else next time.",
            )

            if TASK_LOG_CHANNEL is not None:
                slack_client.chat_postMessage(
                    channel=TASK_LOG_CHANNEL,
                    text=f"Member #{member.member_number} {member.firstname} {member.lastname} reported they couldn't do the task <https://trello.com/c/{card.id}|{log.card_name}>: {sub_action}",
                )
            return {"message": "Marked as not completed"}
    elif action_type == "task_feedback_new_task":
        if sub_action != "new_task":
            raise BadRequest(f"Invalid sub-action '{sub_action}'")

        if log.action == "completed":
            # If the task was already completed, then give the member a new task instead of replacing the old one
            # This can happen if the member clicks "I can do something else too" after already marking the task done
            delegate_task_for_member(
                member.member_id, slack_interaction=None, force=True, ignore_reasons=ignore_reasons
            )
        else:
            log.action = "not_done_rerolled"
            logger.info(f"Member #{member.member_number} {member.firstname} {member.lastname} requested a new task")
            db_session.commit()

            delegate_task_for_member(member.member_id, slack_interaction=payload, ignore_reasons=ignore_reasons)

            trello.add_comment_to_card(
                log.card_id,
                f"Member #{member.member_number} {member.firstname} {member.lastname} wanted a different task",
            )

            if TASK_LOG_CHANNEL is not None:
                slack_client.chat_postMessage(
                    channel=TASK_LOG_CHANNEL,
                    text=f"Member #{member.member_number} {member.firstname} {member.lastname} wanted a different task than <https://trello.com/c/{card.id}|{log.card_name}>",
                )

        return {"message": "Assigned new task"}
    else:
        raise BadRequest(f"Unknown action '{sub_action}'")
