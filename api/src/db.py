from sqlalchemy import create_engine

from config import config, get_db_engine_config
from service import logger
from util import wait_for, can_connect


# TODO Make sure app survives db disconnect.

# TODO Move somewhere not really good structure.
def connect():
    host = config.get('MYSQL_HOST')
    port = int(config.get('MYSQL_PORT'))

    logger.info(f"waiting for db to respond at {host}:{port}")
    if not wait_for(lambda: can_connect(host, port), timeout=24, interval=0.5):
        raise Exception(f"could not connect to db at {host}:{port}")
    
    return create_engine(get_db_engine_config())
