import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import schedule
from rocky.process import log_exception, stoppable
from sqlalchemy.orm import sessionmaker

from multiaccessy.accessy import DummyAccessySession
from service.config import get_mysql_config
from service.db import create_mysql_engine, db_session
from service.logging import logger
from shop.transactions import ship_orders


def ship():
    logger.info("shipping orders")
    try:
        ship_orders()
    except Exception as e:
        logger.exception(f"failed to ship orders: {e}")


def sync():
    logger.info("syncing accessy X")
    try:
        pass  # TODO
    except Exception as e:
        logger.exception(f"failed to sync with accessy: {e}")


if __name__ == '__main__':
    with log_exception(status=1), stoppable():
        parser = ArgumentParser(description="Sync accessy and ship labaccess orders.",
                                formatter_class=ArgumentDefaultsHelpFormatter)
        
        args = parser.parse_args()
        
        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # TODO Enable when we have accessy in place: schedule.every().tuesday.at("19:30").do(ship)
        schedule.every().day.at("04:00").do(sync)
        schedule.every().minute.do(sync)

        while True:
            time.sleep(1)
            schedule.run_pending()
