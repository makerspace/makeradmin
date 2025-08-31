import signal
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime
from logging import getLogger
from threading import Event
from typing import Any

import schedule
from multiaccessy.sync import sync
from rocky.process import log_exception, stoppable
from service.config import get_mysql_config
from service.db import create_mysql_engine, db_session
from shop.transactions import ship_orders
from sqlalchemy.orm import sessionmaker

logger = getLogger("accessy-syncer")

COMMAND_SCHEDULED = "sheduled"
COMMAND_SHIP = "ship"
COMMAND_SYNC = "sync"

exit = Event()


def handle_signal(signum: int, frame: Any) -> None:
    exit.set()


for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(sig, handle_signal)


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


def main() -> None:
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

                while not exit.is_set():
                    schedule.run_pending()
                    exit.wait(5)

            case _:
                raise Exception(f"unknown command {args.command}")


if __name__ == "__main__":
    main()
