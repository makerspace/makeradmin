from logging import getLogger

from flask import request
from service.api_definition import POST, PUBLIC
from service.config import config
from service.error import BadRequest, UnprocessableEntity
from slack_sdk import WebClient

from alerts import service

logger = getLogger("alerts")

FIRE_ALERT_CHANNEL = config.get("SLACK_FIRE_ALERT_CHANNEL_ID")


@service.route("/pressure_sensor_triggered", method=POST, permission=PUBLIC)
def fire() -> str:
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        logger.error("Slack bot token not configured, but we received an event")
        raise UnprocessableEntity("Slack bot token not configured")
    if not FIRE_ALERT_CHANNEL:
        logger.error("Slack fire alert channel not configured, but we received an fire alert event")
        raise UnprocessableEntity("Slack fire alert channel not configured")

    slack_client = WebClient(token=token)

    slack_client.chat_postMessage(
        channel=FIRE_ALERT_CHANNEL,
        mrkdwn=True,
        markdown_text=f""":fire: :fire: :fire:\n\n@channel Fire detected in wood workshop dust collector. Dumping 20 liters of water into the dust bin.\n
If you see this and you are at the space, please:
1. Stop working on whatever you are doing.
2. Check the dust bin in the dust collector in the wood workshop to ensure the fire is out.
3. Check the filters inside the machine to ensure they are not smoldering (right above the dust bin).
4. If things are burning and you cannot put out the fire safely, call emergency services immediately.
5. If it's very smoky and you cannot be in the wood workshop safely, evacuate and call emergency services. Let them know that it's not burning, but that you'd appreciate help with ventilation and ensuring it's safe.
6. Unplug the dust collector from power.
7. Alert people on Slack about the situation.
8. Handle any follow-up actions as necessary, including cleaning up water, debris, and similar. People on Slack will be helpful if you have questions.
9. Put up "Out of order" signs on all machines that use the dust collector. As the dust collector will need to be inspected and possibly repaired before further use.
10. Check again that all dust in the dust bin is thoroughly soaked with water. It is surprisingly hard to completely put out all smoldering embers in the dust bin. If you are unsure, add more water.
\n
:fire: :fire: :fire:""",
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
