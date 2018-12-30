#!python

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from contextlib import closing
from datetime import timedelta, datetime

from rocky.process import log_exception
from sqlalchemy.orm import sessionmaker

from service.api_definition import SERVICE_USER_ID
from service.config import get_mysql_config, config, env, docker_env
from service.db import create_mysql_engine
from service.migrate import ensure_migrations_table
from services import services


def clear_permission_cache(session_factory):
    """ Clear permisssion cache as a part of every db_init/restart. """
    with closing(session_factory()) as session:
        session.execute("UPDATE access_tokens SET permissions = NULL")
        session.commit()


def refresh_service_access_token(session_factory):
    """ Clear permisssion cache as a part of every db_init/restart. """
    
    service_token = config.get('API_BEARER', env, docker_env, log_value=False)
    assert service_token, "API_BEARER not configured"
    
    with closing(session_factory()) as session:
        ten_years = timedelta(days=365 * 10)
        session.execute("DELETE FROM access_tokens WHERE access_token = :token", dict(token=service_token))
        session.execute("INSERT INTO access_tokens VALUES (:user_id, :token, :expires, '', NULL, '', :lifetime)",
                        dict(user_id=SERVICE_USER_ID, token=service_token,
                             expires=datetime.utcnow() + ten_years, lifetime=ten_years.total_seconds()))
        session.commit()


if __name__ == '__main__':

    with log_exception(status=1):
        parser = ArgumentParser(description="Migrate all components.", formatter_class=ArgumentDefaultsHelpFormatter)
        args = parser.parse_args()
        
        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        ensure_migrations_table(engine, session_factory)
        
        for path, service in services:
            service.migrate(session_factory)
        
        clear_permission_cache(session_factory)
        
        refresh_service_access_token(session_factory)
