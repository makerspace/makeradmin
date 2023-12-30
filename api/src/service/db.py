from functools import wraps
from typing import Any, Callable, TypeVar, Union, cast

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from service.logging import logger
from service.util import can_connect, wait_for


class SessionFactoryWrapper:
    """This session factory wrapper is useful to be able to create and import the scoped_session db_session_factory
    before connecting to the databse, this is nice because it makes it easy to use a different db for test."""

    def __init__(self):
        self.session_factory = None

    def init_with_engine(self, engine):
        if self.session_factory is None:
            logger.info(f"initializing session factory with engine {engine}")
            self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        else:
            logger.info(f"reinitializing session factory with engine {engine}")
            self.session_factory.configure(bind=engine)

    def __call__(self, *args, **kwargs):
        if self.session_factory is None:
            raise Exception("Need to initialize with engine first")
        return self.session_factory(*args, **kwargs)


db_session_factory = SessionFactoryWrapper()

db_session: Union[Session, scoped_session] = scoped_session(db_session_factory)


def shutdown_session(exception=None):
    db_session.remove()


def create_mysql_engine(
    host=None, port=None, db=None, user=None, pwd=None, timeout=240, isolation_level="REPEATABLE_READ"
):
    logger.info(f"waiting for db to respond at {host}:{port}")
    if not wait_for(lambda: can_connect(host, port), timeout=timeout, interval=0.5):
        raise Exception(f"could not connect to db at {host}:{port} in {timeout} seconds")

    engine = create_engine(
        f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}", pool_recycle=1800, isolation_level=isolation_level
    )

    db_session_factory.init_with_engine(engine)

    return engine


fields_by_index = {}


def populate_fields_by_index(engine):
    """Populate the dict fields_by_index (used for error messages) by inspecting the database."""
    engine_inspect = inspect(engine)
    for table in engine_inspect.get_table_names():
        for index in engine_inspect.get_indexes(table):
            index_name = index["name"]
            column_names = index["column_names"]
            fields_by_index[index_name] = ",".join(column_names)
            fields_by_index[table + "." + index_name] = ",".join(column_names)


F = TypeVar("F", bound=Callable[..., Any])


def nested_atomic(f: F) -> F:
    """Decorator for committing on success and rollback on any exception. NOTE: A subsequent rollback will rollback
    this nested transaction as well, but comitting will not unrollback a rollbacked nested transaction."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            db_session.begin_nested()
            result = f(*args, **kwargs)
            db_session.commit()
            return result
        except Exception:
            db_session.rollback()
            raise

    return cast(F, wrapper)
