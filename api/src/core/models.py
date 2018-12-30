import secrets
from datetime import timedelta, datetime
from string import ascii_letters, digits

from flask import request, g
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

import membership
from service.api_definition import SERVICE, USER
from service.db import db_session
from service.error import TooManyRequests, Unauthorized, NotFound
from service.logging import logger

Base = declarative_base()


# TODO Remove if possible:
#    relations
#    services

class AccessToken(Base):
    # mysql> describe access_tokens;
    # +--------------+------------------+------+-----+---------+-------+
    # | Field        | Type             | Null | Key | Default | Extra |
    # +--------------+------------------+------+-----+---------+-------+
    # | user_id      | int(11)          | NO   | MUL | NULL    |       |
    # | access_token | varchar(32)      | NO   | PRI | NULL    |       |
    # | browser      | varchar(255)     | NO   |     | NULL    |       |
    # | ip           | varchar(255)     | NO   |     | NULL    |       |
    # | expires      | datetime         | NO   |     | NULL    |       |
    # | permissions  | text             | YES  |     | NULL    |       |
    # | lifetime     | int(10) unsigned | NO   |     | 300     |       |
    # +--------------+------------------+------+-----+---------+-------+
    # 7 rows in set (0.01 sec)
    
    __tablename__ = 'access_tokens'
    
    user_id = Column(Integer, index=True, nullable=False)
    access_token = Column(String(32), primary_key=True, nullable=False)
    browser = Column(String(255), nullable=False)
    ip = Column(String(255), nullable=False)
    expires = Column(DateTime, nullable=False)
    permissions = Column(Text)
    lifetime = Column(Integer, nullable=False, default=300)

    def __repr__(self):
        return f'AccessToken(user_id={self.access_token}, access_token={self.access_token})'

    @classmethod
    def create_user_token(self, user_id):
        assert user_id > 0
        
        access_token = self.generate_token()
        expires = datetime.utcnow() + timedelta(minutes=5)
        
        db_session.add(AccessToken(
            user_id=user_id,
            access_token=access_token,
            browser=request.user_agent.string,
            ip=request.remote_addr,
            expires=expires,
            lifetime=int(timedelta(days=14).total_seconds()),
        ))
        
        return dict(access_token=access_token, expires=expires.isoformat())
        
    @classmethod
    def generate_token(self):
        return ''.join(secrets.choice(ascii_letters + digits) for _ in range(32))

    @classmethod
    def remove_token(self, token, user_id):
        assert user_id > 0
        
        if not db_session.query(AccessToken).filter(self.user_id == user_id, self.access_token == token).delete():
            raise NotFound("The access_token you specified could not be found in the database.")
        
        return None

    @classmethod
    def list_for_user(self, user_id):
        return [dict(
            access_token=access_token.access_token,
            browser=access_token.browser,
            ip=access_token.ip,
            expires=access_token.expires.isoformat(),
        ) for access_token in db_session.query(AccessToken).filter(self.user_id == user_id)]

    # TODO This code needs unittests.
    @classmethod
    def authenticate_request(self):
        """ Update global object with user_id and permissions. """
        g.user_id = None
        g.permissions = tuple()

        # TODO
        # logger.info("DATA " + repr(request.get_data()))
        # logger.info("HEADERS " + repr(request.headers))
        # logger.info("ARGS " + repr(request.args))
        # logger.info("FORM " + repr(request.form))
        # logger.info("JSON " + repr(request.json))
        
        authorization = request.headers.get('Authorization', None)
        if authorization is None:
            return

        bearer = 'Bearer '
        if not authorization.startswith(bearer):
            raise Unauthorized("Unauthorized, can't find credentials.")
            
        token = authorization[len(bearer):].strip()
        
        access_token = db_session.query(AccessToken).get(token)
        if not access_token:
            raise Unauthorized("Unauthorized, invalid access token.")
        
        if access_token.permissions is None:
            permissions = {
                p['permission'] for p in membership.service.service_get(f'/member/{access_token.user_id}/permissions')
            }
            if access_token.user_id < 0:
                permissions.add(SERVICE)
            else:
                permissions.add(USER)
                
            access_token.permissions = ','.join(permissions)
        
        access_token.ip = request.remote_addr
        access_token.browser = request.user_agent.string
        access_token.expires = datetime.utcnow() + timedelta(seconds=access_token.lifetime)
        
        g.user_id = access_token.user_id
        g.permissions = access_token.permissions.split(',')
        
        # Commit token validation to make it stick even if request fails later.
        db_session.commit()
        
        # TODO Where is expiry checked? Remove it if not used?


class Login:
    # login table does not have a possible primary key, so no sqlalchemy model
    # +---------+--------------+------+-----+-------------------+-------------------+
    # | Field   | Type         | Null | Key | Default           | Extra             |
    # +---------+--------------+------+-----+-------------------+-------------------+
    # | success | tinyint(1)   | NO   |     | NULL              |                   |
    # | user_id | int(11)      | YES  |     | NULL              |                   |
    # | ip      | varchar(255) | NO   |     | NULL              |                   |
    # | date    | datetime     | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
    # +---------+--------------+------+-----+-------------------+-------------------+
    
    @staticmethod
    def check_should_throttle(ip):
        """ Raises api exception if this ip has too many failed logins lately. """
        
        count, = db_session.execute("SELECT count(1) FROM login"
                                    "   WHERE ip = :ip AND NOT success AND date >= DATE_SUB(NOW(), INTERVAL 1 HOUR)",
                                    {'ip': ip}).fetchone()
        if count > 10:
            raise TooManyRequests("Your have reached your maximum number of failed login attempts for the last hour."
                                  " Please try again later.")

    @staticmethod
    def register_login_failed(ip):
        db_session.execute("INSERT INTO login (success, ip) VALUES (0, :ip)", {'ip': ip})

    @staticmethod
    def register_login_success(ip, user_id):
        db_session.execute("INSERT INTO login (success, user_id, ip) VALUES (1, :user_id, :ip)",
                           {'user_id': user_id, 'ip': ip})
        
