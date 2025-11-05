import signal
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime
from logging import getLogger
from threading import Event
from typing import Any

import schedule
from multiaccessy.accessy import accessy_session
from multiaccessy.sync import sync
from redis_cache import redis_connection
from rocky.process import log_exception, stoppable
from service.config import get_mysql_config
from service.db import create_mysql_engine, db_session
from shop.transactions import ship_orders
from sqlalchemy.orm import sessionmaker

logger = getLogger("accessy-syncer")

COMMAND_SCHEDULED = "sheduled"
COMMAND_SHIP = "ship"
COMMAND_SYNC = "sync"
COMMAND_DELEGATE = "delegate"

REDIS_COMMAND_QUEUE = "accessy_commands_zset"


def enqueue_command(command: str, timestamp: float) -> None:
    """Add a command to the sorted set with a timestamp."""
    command_key = f"{command}:{timestamp}"  # Unique key for each command-timestamp pair
    logger.info(f"Enqueuing command '{command}' with timestamp {timestamp}")
    redis_connection.zadd(REDIS_COMMAND_QUEUE, {command_key: timestamp})


def deferred_sync() -> None:
    """Enqueue a sync command to be run by the main loop."""
    enqueue_command(COMMAND_SYNC, time.time())


def deferred_delegate() -> None:
    from tasks.delegate import ASSIGNMENT_DELAY_AFTER_START_OF_VISIT

    """Enqueue a delegate command to be run by the main loop."""
    MARGIN = 5  # seconds
    enqueue_command(COMMAND_DELEGATE, time.time() + ASSIGNMENT_DELAY_AFTER_START_OF_VISIT.total_seconds() + MARGIN)


def scheduled_ship() -> None:
    logger.info("shipping orders")
    try:
        ship_orders()
        db_session.commit()
    except Exception as e:
        logger.exception(f"failed to ship orders: {e}")
    finally:
        db_session.remove()
    logger.info("finished shipping orders")


def scheduled_sync() -> None:
    logger.info("syncing accessy")
    try:
        sync()
        db_session.commit()
    except Exception as e:
        logger.exception(f"failed to sync with accessy: {e}")
    finally:
        db_session.remove()
    logger.info("finished syncing accessy")


def daily_job() -> None:
    scheduled_ship()
    scheduled_sync()


def hourly_job() -> None:
    if accessy_session is not None:
        # Refresh the pending invitations cache regularly to avoid slowing down
        # any user-facing pages that rely on it
        accessy_session.refresh_pending_invitations()


def run_queued_commands() -> None:
    try:
        now = time.time()
        # Get the earliest command in the sorted set
        commands = redis_connection.zrangebyscore(REDIS_COMMAND_QUEUE, 0, now, start=0, num=1, withscores=True)
        if commands:
            command_key_b, timestamp = commands[0]
            command_key = command_key_b.decode("utf-8")
            command, _ = command_key.rsplit(":", 1)  # Extract the command from the key
            logger.info(f"Running deferred command '{command}' scheduled for {datetime.fromtimestamp(timestamp)}")
            redis_connection.zrem(REDIS_COMMAND_QUEUE, command_key_b)  # Remove the command after fetching

            match command:
                case x if x == COMMAND_SYNC:
                    sync()
                case x if x == COMMAND_SHIP:
                    ship_orders()
                case x if x == COMMAND_DELEGATE:
                    from tasks.delegate import process_new_visits

                    process_new_visits()
                case _:
                    logger.warning(f"Unknown command: {command}")
    except Exception as e:
        logger.exception(f"Error processing command queue: {e}")


def main(exit: Event) -> None:
    with log_exception(status=1), stoppable():
        parser = ArgumentParser(
            description="Sync accessy and ship labaccess orders.", formatter_class=ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            "command",
            type=str,
            nargs="?",
            default=COMMAND_SCHEDULED,
            help=f"The command to run"
            f", {COMMAND_SCHEDULED}: run forever according to schedule"
            f", {COMMAND_SHIP}: ship once (no sync after) then exit"
            f", {COMMAND_SYNC}: sync",
        )
        args = parser.parse_args()

        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        match args.command:
            case x if x == COMMAND_SHIP:
                ship_orders()
                return

            case x if x == COMMAND_SYNC:
                sync()
                return

            case x if x == COMMAND_SCHEDULED:
                schedule.every().day.at("04:00").do(daily_job)
                schedule.every().hour.do(hourly_job)

                while not exit.is_set():
                    schedule.run_pending()
                    run_queued_commands()
                    exit.wait(5)

            case _:
                raise Exception(f"unknown command {args.command}")


if __name__ == "__main__":
    exit = Event()

    def handle_signal(signum: int, frame: Any) -> None:
        exit.set()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, handle_signal)

    main(exit)
