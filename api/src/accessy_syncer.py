import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import schedule
from rocky.process import log_exception, stoppable
from sqlalchemy.orm import sessionmaker

from multiaccessy.sync import sync
from service.config import get_mysql_config
from service.db import create_mysql_engine
from service.logging import logger
from shop.transactions import ship_orders


COMMAND_SCHEDULED = "sheduled"
COMMAND_SHIP = "ship"
COMMAND_SYNC = "sync"


def scheduled_ship():
    logger.info("shipping orders")
    try:
        ship_orders()
        sync()
    except Exception as e:
        logger.exception(f"failed to ship orders: {e}")


def scheduled_sync():
    logger.info("syncing accessy")
    try:
        sync()
    except Exception as e:
        logger.exception(f"failed to sync with accessy: {e}")


def main():
    with log_exception(status=1), stoppable():
        parser = ArgumentParser(description="Sync accessy and ship labaccess orders.",
                                formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument("command", type=str, nargs=1, default=COMMAND_SCHEDULED,
                            help=f"The command to run"
                                 f", {COMMAND_SCHEDULED}: run forever according to schedule"
                                 f", {COMMAND_SHIP}: ship once (no sync after) then exit"
                                 f", {COMMAND_SYNC}: sync")
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
                # # TODO Enable when we have accessy in place: schedule.every().tuesday.at("19:30").do(scheduled_ship)
                schedule.every().day.at("04:00").do(scheduled_sync)
                
                while True:
                    time.sleep(1)
                    schedule.run_pending()


if __name__ == '__main__':
    main()
    