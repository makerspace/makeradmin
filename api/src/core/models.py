from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

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


# TODO Map this in ORM at all?
# class Login(Base):
#     # mysql> describe login;
#     # +---------+--------------+------+-----+-------------------+-------------------+
#     # | Field   | Type         | Null | Key | Default           | Extra             |
#     # +---------+--------------+------+-----+-------------------+-------------------+
#     # | success | tinyint(1)   | NO   |     | NULL              |                   |
#     # | user_id | int(11)      | YES  |     | NULL              |                   |
#     # | ip      | varchar(255) | NO   |     | NULL              |                   |
#     # | date    | datetime     | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
#     # +---------+--------------+------+-----+-------------------+-------------------+
#     # 4 rows in set (0.01 sec)
#
#     __tablename__ = 'login'
#
#     success = Column(Boolean, nullable=False)
#     user_id = Column(Integer)
#     ip = Column(String(255), nullable=False)
#     date = Column(DateTime, default=datetime.utcnow)
    