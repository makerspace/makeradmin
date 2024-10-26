#!python

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from contextlib import closing
from datetime import datetime, timedelta, timezone

from core.auth import generate_token
from core.models import AccessToken
from core.service_users import SERVICE_USERS
from migrate import ensure_migrations_table, run_migrations
from rocky.process import log_exception
from service.config import get_mysql_config
from service.db import create_mysql_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


def clear_permission_cache(session_factory):
    """Clear permisssion cache as a part of every db_init/restart."""
    with closing(session_factory()) as session:
        session.execute("UPDATE access_tokens SET permissions = NULL")
        session.commit()


def refresh_service_access_tokens(session_factory):
    """Clear permisssion cache as a part of every db_init/restart."""

    with closing(session_factory()) as session:
        ten_years = timedelta(days=365 * 10)
        for service_user in SERVICE_USERS:
            if service_user.present:
                try:
                    access_token = session.query(AccessToken).filter_by(user_id=service_user.id).one()

                except NoResultFound:
                    access_token = AccessToken(
                        user_id=service_user.id,
                        access_token=service_user.token or generate_token(),
                        browser="",
                        ip="",
                    )

                except MultipleResultsFound as e:
                    raise Exception(f"Found multiple of service token id {service_user.id}, this is a bug.") from e

                access_token.lifetime = ten_years.total_seconds()
                access_token.expires = datetime.now(timezone.utc) + ten_years

                session.add(access_token)
            else:
                session.query(AccessToken).filter_by(user_id=service_user.id).delete()

            session.commit()


def init_db():
    engine = create_mysql_engine(**get_mysql_config())
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    ensure_migrations_table(engine, session_factory)

    run_migrations(session_factory)

    clear_permission_cache(session_factory)

    refresh_service_access_tokens(session_factory)


if __name__ == "__main__":
    with log_exception(status=1):
        parser = ArgumentParser(description="Migrate all components.", formatter_class=ArgumentDefaultsHelpFormatter)
        args = parser.parse_args()

        init_db()
