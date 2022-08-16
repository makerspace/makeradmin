from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from time import sleep

from rocky.process import log_exception, stoppable
from sqlalchemy.orm import sessionmaker
from api.src.service.config import get_mysql_config
from api.src.service.db import create_mysql_engine, db_session
from service.logging import logger


if __name__ == '__main__':
    with log_exception(status=1), stoppable():
        parser = ArgumentParser(description="Sync accessy and ship labaccess orders.",
                                formatter_class=ArgumentDefaultsHelpFormatter)
        
        args = parser.parse_args()
        
        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info(f'checking for emails to send every {args.sleep} seconds, limit is {args.limit}')
        
        while True:
            sleep(100)
            try:
                # TODO sync accessy every day
                # TODO ship order periodically, ask board for when
                pass
            except Exception as e:
                logger.warning(f"failed to do db query. ignoring: {e}")
            finally:
                db_session.remove()
