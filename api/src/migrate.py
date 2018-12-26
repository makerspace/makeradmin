#!python

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from rocky.process import log_exception
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from db import connect
from service import migrate
#from config import SERVICE_CONFIGS


with log_exception(status=1):
    parser = ArgumentParser(description="Migrate all components.", formatter_class=ArgumentDefaultsHelpFormatter)
    args = parser.parse_args()
    
    engine = connect()
    
    table_names = inspect(engine).get_table_names()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # TODO migrate(session_factory, table_names, SERVICE_CONFIGS)
