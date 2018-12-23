#!python

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from rocky.process import log_exception
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from component import migrate
from config import get_db_engine_config, COMPONENT_CONFIGS

with log_exception(status=1):
    parser = ArgumentParser(description="Migrate all components.", formatter_class=ArgumentDefaultsHelpFormatter)
    args = parser.parse_args()
    
    engine = create_engine(get_db_engine_config())
    table_names = inspect(engine).get_table_names()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    migrate(session_factory, table_names, COMPONENT_CONFIGS)
