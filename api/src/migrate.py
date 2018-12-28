#!python

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from rocky.process import log_exception
from sqlalchemy.orm import sessionmaker

from service.config import get_mysql_config
from service.db import create_mysql_engine
from service.migrate import ensure_migrations_table
from services import services


with log_exception(status=1):
    parser = ArgumentParser(description="Migrate all components.", formatter_class=ArgumentDefaultsHelpFormatter)
    args = parser.parse_args()
    
    engine = create_mysql_engine(**get_mysql_config())
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    ensure_migrations_table(engine, session_factory)
    
    for path, service in services:
        service.migrate(session_factory)
