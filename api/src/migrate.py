#!python

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from rocky.process import log_exception
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from service import migrate, logger
from config import get_db_engine_config, SERVICE_CONFIGS, config
from util import can_connect, wait_for

with log_exception(status=1):
    parser = ArgumentParser(description="Migrate all components.", formatter_class=ArgumentDefaultsHelpFormatter)
    args = parser.parse_args()

    host = config.get('MYSQL_HOST')
    port = int(config.get('MYSQL_PORT'))

    logger.info(f"waiting for db to respond at {host}:{port}")
    if not wait_for(lambda: can_connect(host, port), timeout=24, interval=0.5):
        raise Exception(f"could not connect to db at {host}:{port}")
    
    engine = create_engine(get_db_engine_config())
    
    table_names = inspect(engine).get_table_names()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    migrate(session_factory, table_names, SERVICE_CONFIGS)
