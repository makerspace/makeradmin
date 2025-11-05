import json
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

from tasks import service, trello
from tasks.delegate import SlackInteraction, delegate_task_for_member
from tasks.models import TaskDelegationLog

logger = getLogger("task-delegator")


@service.route("/slack/interaction", method=POST, permission=PUBLIC)  # PUBLIC because Slack posts here
def slack_interaction() -> dict:
    """
    Slack interaction endpoint.
    Expects 'payload' form param with JSON body from Slack.
    button value format: "{log_id}:done" or "{log_id}:skip"
    """
    json = request.form.get("payload")
    if not json:
        raise BadRequest("Missing JSON payload")
    logger.info(f"Received Slack interaction payload:\n{json}")
    payload = from_json(SlackInteraction, json)
    action_type = payload.action.action_id
    parts = payload.action.value.split(":")

    log_id = int(parts[0])
    sub_action = parts[1]

    log = db_session.get(TaskDelegationLog, log_id)
    if not log:
        raise NotFound("no such task has been delegated")

    member = db_session.get(Member, log.member_id)
    assert member is not None

    token = config.get("SLACK_BOT_TOKEN")
    slack_client = WebClient(token=token)

    if action_type == "task_feedback_done":
        if sub_action != "done":
            raise BadRequest(f"Invalid sub-action '{sub_action}'")
        # Update log and move trello card
        log.action = "completed"
        trello.move_card_to_done(log.card_id)
        trello.add_comment_to_card(
            log.card_id, f"Marked completed by member #{member.member_number} {member.firstname} {member.lastname}"
        )
        db_session.add(log)
        db_session.commit()

        slack_client.chat_update(
            channel=payload.channel,
            ts=payload.message.ts,
            text="Thank you! The task has been marked as completed.",
            blocks=[],
        )
        return {"message": "Thanks — marked done"}
    elif action_type == "task_feedback_not_done":
        if sub_action not in get_args(TaskDelegationLog.ACTION_TYPE):
            raise BadRequest(f"Invalid sub-action '{sub_action}'")
        log.action = cast(TaskDelegationLog.ACTION_TYPE, sub_action)
        db_session.add(log)
        db_session.commit()
        trello.add_comment_to_card(
            log.card_id,
            f"Member #{member.member_number} {member.firstname} {member.lastname} reported they couldn't do the task: {sub_action}",
        )

        slack_client.chat_update(
            channel=payload.channel,
            ts=payload.message.ts,
            text="No worries, thanks for letting us know. We'll give you something else next time.",
            blocks=[],
        )
        return {"message": "Marked as not completed"}
    elif action_type == "task_feedback_new_task":
        if sub_action != "new_task":
            raise BadRequest(f"Invalid sub-action '{sub_action}'")

        log.action = cast(TaskDelegationLog.ACTION_TYPE, "not_done_other")  # TODO: Replace by "rerolled" or something
        db_session.add(log)
        db_session.commit()
        trello.add_comment_to_card(
            log.card_id,
            f"Member #{member.member_number} {member.firstname} {member.lastname} reported they wanted a different task",
        )

        delegate_task_for_member(member.member_id, payload)
        return {"message": "Assigned new task"}
    else:
        raise BadRequest(f"Unknown action '{sub_action}'")
