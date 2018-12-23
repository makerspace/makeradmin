from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Member(Base):
    # mysql> describe membership_members;
    # +-----------------+------------------+------+-----+-------------------+-------------------+
    # | Field           | Type             | Null | Key | Default           | Extra             |
    # +-----------------+------------------+------+-----+-------------------+-------------------+
    # | member_id       | int(10) unsigned | NO   | PRI | NULL              | auto_increment    |
    # | email           | varchar(255)     | NO   | MUL | NULL              |                   |
    # | password        | varchar(60)      | YES  |     | NULL              |                   |
    # | firstname       | varchar(255)     | NO   |     | NULL              |                   |
    # | lastname        | varchar(255)     | YES  |     | NULL              |                   |
    # | civicregno      | varchar(12)      | YES  |     | NULL              |                   |
    # | company         | varchar(255)     | YES  |     | NULL              |                   |
    # | orgno           | varchar(12)      | YES  |     | NULL              |                   |
    # | address_street  | varchar(255)     | YES  |     | NULL              |                   |
    # | address_extra   | varchar(255)     | YES  |     | NULL              |                   |
    # | address_zipcode | int(11)          | YES  |     | NULL              |                   |
    # | address_city    | varchar(255)     | YES  |     | NULL              |                   |
    # | address_country | varchar(2)       | YES  |     | NULL              |                   |
    # | phone           | varchar(255)     | YES  |     | NULL              |                   |
    # | created_at      | datetime         | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
    # | updated_at      | datetime         | YES  |     | NULL              |                   |
    # | deleted_at      | datetime         | YES  |     | NULL              |                   |
    # | member_number   | int(11)          | NO   |     | NULL              |                   |
    # +-----------------+------------------+------+-----+-------------------+-------------------+
    # 18 rows in set (0.00 sec)

    __tablename__ = 'membership_members'
    
    member_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(60))
    firstname = Column(String(255), nullable=False)
    lastname = Column(String(255))
    civicregno = Column(String(12))
    company = Column(String(255))
    orgno = Column(String(12))
    address_street = Column(String(255))
    address_extra = Column(String(255))
    address_zipcode= Column(Integer)
    address_city = Column(String(255))
    address_country = Column(String(2))
    phone = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    member_number = Column(Integer)

    def __repr__(self):
        return f'Member(member_id={self.member_id}, member_number={self.member_number}, email={self.email})'
