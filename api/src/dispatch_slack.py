"""
Slack message dispatcher.

This module handles sending queued Slack messages from the database.
Similar to dispatch_emails.py but for Slack messages.
"""

import json
import signal
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime, timezone
from logging import getLogger
from threading import Event
from time import sleep
from typing import Any

from messages.models import Message
from rocky.process import log_exception, stoppable
from service.config import config, get_mysql_config
from service.db import create_mysql_engine, db_session
from slack.util import get_slack_client, lookup_slack_user_by_email
from slack_sdk.errors import SlackApiError
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

logger = getLogger("slack-dispatcher")


class NoSlackAuthConfigured(Exception):
    pass


def send_slack_messages(limit: int) -> None:
    """
    Send queued Slack messages from the database.

    Args:
        limit: Maximum number of messages to send in this batch
    """
    query = db_session.query(Message)
    query = query.filter(Message.status == Message.QUEUED)
    query = query.filter(Message.recipient_type == "slack")
    query = query.limit(limit)

    slack_client = get_slack_client()
    skipped_messages = []

    for message in query:
        recipient_email = message.recipient
        msg = f"sending Slack message {message.id} to {recipient_email}"

        if not slack_client:
            skipped_messages.append(message)
            continue

        try:
            # Look up Slack user by email
            slack_user_id = lookup_slack_user_by_email(slack_client, recipient_email)
            if not slack_user_id:
                logger.error(f"Could not find Slack user for email {recipient_email}")
                message.status = Message.FAILED
                db_session.add(message)
                db_session.commit()
                continue

            msg += f" (Slack user {slack_user_id}): {message.subject}"

            # Parse blocks from message body (stored as JSON)
            # chat_postMessage accepts Block objects, dicts, or lists of dicts
            try:
                blocks = json.loads(message.body)
                if not isinstance(blocks, list):
                    raise ValueError("Blocks must be a list")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse Slack blocks from message {message.id}: {e}")
                message.status = Message.FAILED
                db_session.add(message)
                db_session.commit()
                continue

            # Send the message with retries on connection errors
            while True:
                try:
                    slack_client.chat_postMessage(
                        channel=slack_user_id,
                        text=message.subject,  # Fallback text for notifications
                        blocks=blocks,
                    )
                    break
                except SlackApiError as e:
                    if e.response["error"] in ["ratelimited", "internal_error"]:
                        # Retry on rate limit or internal errors
                        logger.warning(f"Temporary Slack error. Retrying in a few seconds: {e}\n")
                        sleep(5)
                    else:
                        # Don't retry on other errors (user not found, invalid blocks, etc.)
                        raise

            logger.info(msg)
            message.status = Message.SENT
            message.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db_session.add(message)
            db_session.commit()

        except SlackApiError as e:
            logger.error(f"Failed to send Slack message {message.id} to {recipient_email}: {e.response['error']}")
            message.status = Message.FAILED
            db_session.add(message)
            db_session.commit()
        except Exception as e:
            logger.error(f"Unexpected error sending Slack message {message.id}: {e}")
            message.status = Message.FAILED
            db_session.add(message)
            db_session.commit()

    if len(skipped_messages) > 0:
        logger.warning(
            f"Skipped sending {len(skipped_messages)} Slack messages because no SLACK_BOT_TOKEN is configured."
        )
        for message in skipped_messages:
            message.status = Message.FAILED
            db_session.add(message)
        db_session.commit()


# Main loop removed - this module is now imported by dispatch_messages.py
