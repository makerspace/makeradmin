from logging import getLogger

from flask import request
from service.api_definition import POST, PUBLIC
from service.config import config
from service.error import BadRequest, UnprocessableEntity
from slack_sdk import WebClient

from alerts import service

logger = getLogger("alerts")

FIRE_ALERT_CHANNEL = "C09S5J35FME"


@service.route("/pressure_sensor_triggered", method=POST, permission=PUBLIC)
def fire() -> str:
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        logger.error("Slack bot token not configured, but we received an event")
        raise BadRequest("Slack bot token not configured")

    slack_client = WebClient(token=token)

    slack_client.chat_postMessage(
        channel=FIRE_ALERT_CHANNEL,
        mrkdwn=True,
        markdown_text=f":fire: :fire: :fire:\n\nFire detected in wood workshop dust collector. Dumping 20 liters of water into the dust bin.\n\n:fire: :fire: :fire:",
    )
    return "Alert sent"


@service.route("/pressure_sensor_reset", method=POST, permission=PUBLIC)
def fire_reset() -> str:
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        logger.error("Slack bot token not configured, but we received an event")
        raise BadRequest("Slack bot token not configured")

    slack_client = WebClient(token=token)

    slack_client.chat_postMessage(
        channel=FIRE_ALERT_CHANNEL,
        mrkdwn=True,
        markdown_text=f"Pressure sensor in wood workshop dust collector has been reset. Presumably someone just refilled the sprinkler system with water. Good work!",
    )
    return "Alert sent"
