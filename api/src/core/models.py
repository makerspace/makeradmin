import secrets
from datetime import timedelta, datetime
from string import ascii_letters, digits

from flask import request
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

from service.db import db_session
from service.error import TooManyRequests

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
            browser=request.user_agent,
            ip=request.remote_addr,
            expires=expires,
            lifetime=int(timedelta(days=14).total_seconds()),
        ))
        
        return dict(access_token=access_token, expires=expires.isoformat())
        
    @classmethod
    def generate_token(self):
        return ''.join(secrets.choice(ascii_letters + digits) for _ in range(32))


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
        
