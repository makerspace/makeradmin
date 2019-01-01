from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, Date, Enum
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


class Group(Base):
    # mysql> describe membership_groups;
    # +-------------+------------------+------+-----+-------------------+-------------------+
    # | Field       | Type             | Null | Key | Default           | Extra             |
    # +-------------+------------------+------+-----+-------------------+-------------------+
    # | group_id    | int(10) unsigned | NO   | PRI | NULL              | auto_increment    |
    # | parent      | int(11)          | NO   | MUL | NULL              |                   |
    # | left        | int(11)          | NO   | MUL | NULL              |                   |
    # | right       | int(11)          | NO   | MUL | NULL              |                   |
    # | name        | varchar(255)     | NO   |     | NULL              |                   |
    # | title       | varchar(255)     | NO   |     | NULL              |                   |
    # | description | text             | YES  |     | NULL              |                   |
    # | created_at  | datetime         | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
    # | updated_at  | datetime         | YES  |     | NULL              |                   |
    # | deleted_at  | datetime         | YES  |     | NULL              |                   |
    # +-------------+------------------+------+-----+-------------------+-------------------+
    # 10 rows in set (0.00 sec)

    __tablename__ = 'membership_groups'
    
    group_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    parent = Column(Integer, index=True, nullable=False)  # TODO What is this?
    left = Column(Integer, index=True, nullable=False)  # TODO What is this?
    right = Column(Integer, index=True, nullable=False)  # TODO What is this?
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)


class Permission(Base):
    # mysql> describe membership_permissions;
    # +---------------+------------------+------+-----+-------------------+-------------------+
    # | Field         | Type             | Null | Key | Default           | Extra             |
    # +---------------+------------------+------+-----+-------------------+-------------------+
    # | permission_id | int(10) unsigned | NO   | PRI | NULL              | auto_increment    |
    # | role_id       | int(11)          | NO   |     | 0                 |                   |
    # | permission    | varchar(255)     | NO   | UNI | NULL              |                   |
    # | group_id      | int(11)          | NO   |     | 0                 |                   |
    # | created_at    | datetime         | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
    # | updated_at    | datetime         | YES  |     | NULL              |                   |
    # | deleted_at    | datetime         | YES  |     | NULL              |                   |
    # +---------------+------------------+------+-----+-------------------+-------------------+
    # 7 rows in set (0.00 sec)

    __tablename__ = 'membership_permissions'

    permission_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    role_id = Column(Integer, nullable=False)  # TODO Foreigh key? Ditch roles?
    permission = Column(String(255), nullable=False, unique=True)
    group_id = Column(Integer,  nullable=False)  # TODO Foreign key. What is this? Not many to many?
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)


# TODO Many to many
# mysql> describe membership_group_permissions;
# +---------------+------------------+------+-----+---------+----------------+
# | Field         | Type             | Null | Key | Default | Extra          |
# +---------------+------------------+------+-----+---------+----------------+
# | id            | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
# | group_id      | int(10) unsigned | NO   | MUL | NULL    |                |
# | permission_id | int(10) unsigned | NO   | MUL | NULL    |                |
# +---------------+------------------+------+-----+---------+----------------+
# 3 rows in set (0.00 sec)


class Key(Base):
    
    # mysql> describe membership_keys;
    # +-------------+------------------+------+-----+-------------------+-------------------+
    # | Field       | Type             | Null | Key | Default           | Extra             |
    # +-------------+------------------+------+-----+-------------------+-------------------+
    # | rfid_id     | int(10) unsigned | NO   | PRI | NULL              | auto_increment    |
    # | member_id   | int(10) unsigned | NO   | MUL | NULL              |                   |
    # | description | text             | YES  |     | NULL              |                   |
    # | tagid       | varchar(255)     | NO   | MUL | NULL              |                   |
    # | created_at  | datetime         | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
    # | updated_at  | datetime         | YES  |     | NULL              |                   |
    # | deleted_at  | datetime         | YES  |     | NULL              |                   |
    # +-------------+------------------+------+-----+-------------------+-------------------+
    # 7 rows in set (0.00 sec)
    
    __tablename__ = 'membership_keys'

    rfid_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, nullable=False)  # TODO Foreigh key? Index.
    description = Column(Text)
    tagid = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
# TODO Many to many.
# mysql> describe membership_members_groups;
# +-----------+---------+------+-----+---------+-------+
# | Field     | Type    | Null | Key | Default | Extra |
# +-----------+---------+------+-----+---------+-------+
# | member_id | int(11) | NO   | PRI | NULL    |       |
# | group_id  | int(11) | NO   | PRI | NULL    |       |
# +-----------+---------+------+-----+---------+-------+
# 2 rows in set (0.00 sec)


class Span(Base):
    # mysql> describe membership_spans;
    # +-----------------+------------------------+------+-----+-------------------+-------------------+
    # | Field           | Type                   | Null | Key | Default           | Extra             |
    # +-----------------+------------------------+------+-----+-------------------+-------------------+
    # | span_id         | int(10) unsigned       | NO   | PRI | NULL              | auto_increment    |
    # | member_id       | int(10) unsigned       | NO   | MUL | NULL              |                   |
    # | startdate       | date                   | NO   |     | NULL              |                   |
    # | enddate         | date                   | NO   |     | NULL              |                   |
    # | type            | enum('labaccess','memb | NO   |     | NULL              |                   |
    # | creation_reason | varchar(255)           | YES  |     | NULL              |                   |
    # | created_at      | datetime               | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
    # | deleted_at      | timestamp              | YES  |     | NULL              |                   |
    # | deletion_reason | varchar(255)           | YES  |     | NULL              |                   |
    # +-----------------+------------------------+------+-----+-------------------+-------------------+
    # 9 rows in set (0.00 sec)

    __tablename__ = 'membership_spans'

    span_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, nullable=False)  # TODO Foreigh key?
    startdate = Column(Date, nullable=False)  # Start date, inclusive
    enddate = Column(Date, nullable=False)    # End date, inclusive
    type = Column(Enum('labaccess', 'membership', 'special_labaccess'), nullable=False)
    creation_reason = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    





