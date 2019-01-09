from typing import Union

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, Session, sessionmaker

from service.logging import logger
from service.util import wait_for, can_connect


class SessionFactoryWrapper:
    """ This session factory wrapper is useful to be able to create and import the scoped_session db_session_factory
    before connecting to the databse, this is nice because it makes it easy to use a different db for test. """
    
    def __init__(self):
        self.session_factory = None
        
    def init_with_engine(self, engine):
        self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
    def __call__(self, *args, **kwargs):
        return self.session_factory(*args, **kwargs)
        

db_session_factory = SessionFactoryWrapper()

db_session: Union[Session, scoped_session] = scoped_session(db_session_factory)


def shutdown_session(exception=None):
    db_session.remove()


def create_mysql_engine(host=None, port=None, db=None, user=None, pwd=None, timeout=24):
    logger.info(f"waiting for db to respond at {host}:{port}")
    if not wait_for(lambda: can_connect(host, port), timeout=timeout, interval=0.5):
        raise Exception(f"could not connect to db at {host}:{port} in {timeout} seconds")
    
    engine = create_engine(f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}")
    
    db_session_factory.init_with_engine(engine)
    
    return engine


fields_by_index = {}


def populate_fields_by_index(engine):
    """ Populate the dict fields_by_index (used for error messages) by inspecting the database. """
    entine_inspect = inspect(engine)
    for table in entine_inspect.get_table_names():
        for index in entine_inspect.get_indexes(table):
            fields_by_index[index['name']] = ",".join(index['column_names'])
    