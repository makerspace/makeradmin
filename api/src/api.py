import os
from datetime import datetime
from random import choice, seed
from string import ascii_letters, digits
from typing import Union

from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from component import logger
from config import get_db_engine_config, config
from core.models import Base as CoreBase, AccessToken
from membership.models import Base as MembershipBase, Member
from util import wait_for, can_connect

app = Flask(__name__)

# TODO Duplicate code
host = config.get('MYSQL_HOST')
port = int(config.get('MYSQL_PORT'))
logger.info(f"waiting for db to respond at {host}:{port}")
if not wait_for(lambda: can_connect(host, port), timeout=8, interval=0.5):
    raise Exception(f"could not connect to db at {host}:{port}")
engine = create_engine(get_db_engine_config())
# TODO Make sure app survives db disconnect.

session: Union[Session, scoped_session] = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
# TODO Base.query = db_session.query_property()


@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()
    
    
# CoreBase.metadata.create_all(bind=engine)
# MembershipBase.metadata.create_all(bind=engine)


seed(os.urandom(8))


def random_str(length=12):
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


# session.add(Member(email=random_str(), firstname=random_str()))
# session.add(AccessToken(access_token=random_str(), user_id=2, browser=random_str(), ip=random_str(),
#                         expires=datetime(2038, 1, 1)))
# session.commit()


# for i in session.query(Member).order_by('member_id'):
#     print(i.email)
#
#
# sql = text("SELECT m.*, a.* FROM membership_members as m LEFT OUTER JOIN access_tokens as a ON m.member_id == a.user_id")
#
# for m, a in session.query(Member, AccessToken).from_statement(sql):
#     print(m.member_id, m.email, (a and a.user_id) or None, (a and a.access_token) or None)
    
    