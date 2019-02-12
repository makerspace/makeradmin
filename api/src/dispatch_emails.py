from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from rocky.process import log_exception
from sqlalchemy.orm import sessionmaker

from service.config import get_mysql_config
from service.db import create_mysql_engine

if __name__ == '__main__':

    with log_exception(status=1):
        parser = ArgumentParser(description="Dispatch emails in db send queue.", 
                                formatter_class=ArgumentDefaultsHelpFormatter)
        args = parser.parse_args()
        
        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
