import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime

import schedule
from multiaccessy.sync import sync
from rocky.process import log_exception, stoppable
from service.config import get_mysql_config
from service.db import create_mysql_engine, db_session
from service.logging import logger
from shop.transactions import ship_orders
from sqlalchemy.orm import sessionmaker

COMMAND_SCHEDULED = "sheduled"
COMMAND_SHIP = "ship"
COMMAND_SYNC = "sync"


def scheduled_ship_and_sync():
    try:
        logger.info("shipping orders")
        ship_orders()
        logger.info("syncing accessy")
        sync()
        db_session.commit()
        logger.info("committing changes to db")
    except Exception as e:
        logger.exception(f"failed to ship orders: {e}")
    finally:
        db_session.remove()


def scheduled_sync():
    logger.info("syncing accessy")
    try:
        sync()
        db_session.commit()
        logger.info("finished syncing accessy")
    except Exception as e:
        logger.exception(f"failed to sync with accessy: {e}")
    finally:
        db_session.remove()


friday = 4


def daily_job():
    if datetime.today().weekday() is friday:
        scheduled_ship_and_sync()
    else:
        scheduled_sync()


def main():
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
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

        logger.info(f"running syncer command {args.command}")

        match args.command:
            case x if x == COMMAND_SHIP:
                ship_orders()
                return

            case x if x == COMMAND_SYNC:
                sync()
                return

            case x if x == COMMAND_SCHEDULED:
                schedule.every().day.at("04:00").do(daily_job)

                while True:
                    time.sleep(1)
                    schedule.run_pending()

            case _:
                raise Exception(f"unknown command {args.command}")


if __name__ == "__main__":
    main()
