#!python

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from contextlib import closing
from datetime import timedelta, datetime

from rocky.process import log_exception
from sqlalchemy.orm import sessionmaker

from service.api_definition import SERVICE_USER_ID
from service.config import get_mysql_config, config
from service.db import create_mysql_engine
from migrate import ensure_migrations_table, run_migrations


def clear_permission_cache(session_factory):
    """ Clear permisssion cache as a part of every db_init/restart. """
    with closing(session_factory()) as session:
        session.execute("UPDATE access_tokens SET permissions = NULL")
        session.commit()


def refresh_service_access_token(session_factory):
    """ Clear permisssion cache as a part of every db_init/restart. """
    
    service_token = config.get('API_BEARER', log_value=False)
    assert service_token, "API_BEARER not configured"
    
    with closing(session_factory()) as session:
        ten_years = timedelta(days=365 * 10)
        session.execute("DELETE FROM access_tokens WHERE user_id = :user_id", dict(user_id=SERVICE_USER_ID))
        session.execute("INSERT INTO access_tokens (user_id, access_token, expires, lifetime, browser, ip)"
                        "   VALUES (:user_id, :token, :expires, :lifetime, '', '')",
                        dict(user_id=SERVICE_USER_ID, token=service_token,
                             expires=datetime.utcnow() + ten_years, lifetime=ten_years.total_seconds()))
        session.commit()


def init_db():
    engine = create_mysql_engine(**get_mysql_config())
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    ensure_migrations_table(engine, session_factory)
    
    run_migrations(session_factory)
        
    clear_permission_cache(session_factory)
    
    refresh_service_access_token(session_factory)


if __name__ == '__main__':

    with log_exception(status=1):
        parser = ArgumentParser(description="Migrate all components.", formatter_class=ArgumentDefaultsHelpFormatter)
        args = parser.parse_args()
        
        init_db()
