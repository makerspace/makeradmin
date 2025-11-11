import json
from datetime import datetime
from logging import getLogger
from typing import cast, get_args

from flask import request
from membership.models import Member
from serde import from_dict, serde
from serde.json import from_json, to_json
from service.api_definition import POST, PUBLIC
from service.config import config
from service.db import db_session
from service.error import BadRequest, NotFound
from slack_sdk import WebClient
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
)
from tasks.models import TaskDelegationLog

logger = getLogger("task-delegator")


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

    return slack_handle_task_feedback(payload)


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

    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        logger.error("Slack bot token not configured, but we received a Slack interaction request")
        raise BadRequest("Slack bot token not configured")

    slack_client = WebClient(token=token)
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

        completion_info = CardCompletionInfo.from_card(card, [])
        requirements = CardRequirements.from_card(card)
        ctx = TaskContext.from_member(member.member_id, now)

        try:
            if not completion_info.infinitely_repeatable:
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
        trello.add_comment_to_card(
            log.card_id,
            f"Member #{member.member_number} {member.firstname} {member.lastname} reported they couldn't do the task: {sub_action}",
        )

        slack_client.chat_update(
            channel=payload.channel.id,
            ts=payload.message.ts,
            text=":thumbsup: No worries, thanks for letting us know. We'll give you something else next time.",
            blocks=[],
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
            logger.info(f"Action {log.action} saved to DB for log {log.id}")

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
