"""
Unified message dispatcher.

This module coordinates the dispatching of all message types (email, SMS, Slack).
It handles scheduling reminder messages and dispatching queued messages.
"""

import signal
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import timedelta
from logging import getLogger
from threading import Event
from typing import Any

from dispatch_emails import (
    labaccess_reminder,
    memberbooth_labels,
    membership_reminder,
    quiz_reminders,
    schedule_messages,
    send_messages,
)
from dispatch_slack import send_slack_messages
from rocky.process import log_exception, stoppable
from service.config import config, get_mysql_config
from service.db import create_mysql_engine, db_session
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

logger = getLogger("message-dispatcher")

if __name__ == "__main__":
    exit = Event()

    def handle_signal(signum: int, frame: Any) -> None:
        logger.error(f"Got signal {signum}, exiting...")
        exit.set()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, handle_signal)

    with log_exception(status=1), stoppable():
        parser = ArgumentParser(
            description="Dispatch all message types (email, SMS, Slack) from db send queue.",
            formatter_class=ArgumentDefaultsHelpFormatter,
        )

        parser.add_argument("--sleep", default=1, help="Sleep time (in seconds) between doing any work.")
        parser.add_argument("--limit", default=4, help="Max messages to send every time checking for messages.")

        args = parser.parse_args()

        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        logger.info(f"Checking for messages to send every {args.sleep} seconds, limit is {args.limit}")

        # Email configuration (Mailgun)
        mailgun_key = config.get("MAILGUN_KEY", log_value=False)
        if mailgun_key is not None and mailgun_key.strip() == "":
            mailgun_key = None

        mailgun_domain = config.get("MAILGUN_DOMAIN")
        mailgun_sender = config.get("MAILGUN_FROM")
        mailgun_to_override = config.get("MAILGUN_TO_OVERRIDE")
        last_reminder_check = -10000.0

        # Don't send messages immediately, to avoid clobbering up the logs
        # And also for API to start up and any migrations to run
        exit.wait(10)

        while not exit.is_set():
            try:
                # Schedule reminder messages (hourly)
                if time.time() - last_reminder_check > 60 * 60:
                    # These checks are kinda slow (takes a few hundred ms)
                    # so don't do them as often. They are not time critical anyway.
                    last_reminder_check = time.time()
                    logger.info("Checking for reminders to send")
                    labaccess_reminder()
                    membership_reminder()
                    quiz_reminders()
                    db_session.commit()

                # Schedule memberbooth label messages
                schedule_messages(memberbooth_labels(observation_send_delay=timedelta(minutes=5)))

                # Dispatch all message types
                send_messages(mailgun_key, mailgun_domain, mailgun_sender, mailgun_to_override, args.limit)
                send_slack_messages(args.limit)

                db_session.commit()
            except DatabaseError as e:
                logger.warning(f"Failed to do db query. Ignoring: {e}")
            finally:
                db_session.remove()

            exit.wait(args.sleep)
