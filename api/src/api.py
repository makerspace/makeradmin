from typing import Union

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from service import logger
from config import get_db_engine_config, config
from util import wait_for, can_connect

app = Flask(__name__)

# TODO Duplicate code
host = config.get('MYSQL_HOST')
port = int(config.get('MYSQL_PORT'))
logger.info(f"waiting for db to respond at {host}:{port}")
if not wait_for(lambda: can_connect(host, port), timeout=24, interval=0.5):
    raise Exception(f"could not connect to db at {host}:{port}")
engine = create_engine(get_db_engine_config())
# TODO Make sure app survives db disconnect.

session: Union[Session, scoped_session] = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


# TODO Check signature, what happends with exception.
@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()
    

# TODO Use Sentry?