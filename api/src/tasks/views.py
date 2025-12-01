import json
from datetime import datetime, timedelta
from logging import getLogger
from typing import cast, get_args

from flask import request
from membership.models import Member
from serde import from_dict, serde
from serde.json import from_json, to_json
from service.api_definition import POST, PUBLIC
from service.config import config
from service.db import db_session
from service.error import BadRequest, NotFound, UnprocessableEntity
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

from tasks import service, trello
from tasks.delegate import (
    TASK_LOG_CHANNEL,
    CardCompletionInfo,
    CardRequirements,
    SlackInteraction,
    TaskContext,
    delegate_task_for_member,
    get_all_room_labels,
    member_recently_received_task,
    visit_events_by_member_id,
)
from tasks.models import MemberPreference, MemberPreferenceQuestionType, TaskDelegationLog

logger = getLogger("task-delegator")


def member_from_slack_user_id(slack_client: WebClient, slack_user_id: str) -> Member | None:
    """Get Member object from Slack user ID."""
    try:
        user_info = slack_client.users_info(user=slack_user_id)
        email = user_info["user"]["profile"]["email"]
    except SlackApiError as e:
        logger.error(f"Failed to get Slack user info: {e.response['error']}")
        raise BadRequest("Failed to get user info from Slack")

    return db_session.execute(select(Member).where(Member.email == email)).scalar_one_or_none()


def get_slack_client() -> WebClient:
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        raise UnprocessableEntity("Slack bot token not configured")
    return WebClient(token=token)


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
            log.action = "not_done_other"  # TODO: Replace by "rerolled" or something
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
