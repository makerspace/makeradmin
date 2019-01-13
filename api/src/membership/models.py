import bcrypt
from sqlalchemy import Column, Integer, String, DateTime, Text, Date, Enum, Table, ForeignKey, func, text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, column_property

from service.api_definition import BAD_VALUE
from service.db import db_session
from service.error import Unauthorized

Base = declarative_base()


member_group = Table(
    # mysql> describe membership_members_groups;
    # +-----------+---------+------+-----+---------+-------+
    # | Field     | Type    | Null | Key | Default | Extra |
    # +-----------+---------+------+-----+---------+-------+
    # | member_id | int(11) | NO   | PRI | NULL    |       |
    # | group_id  | int(11) | NO   | PRI | NULL    |       |
    # +-----------+---------+------+-----+---------+-------+
    'membership_members_groups',
    Base.metadata,
    Column('member_id', ForeignKey('membership_members.member_id'), primary_key=True),
    Column('group_id', ForeignKey('membership_groups.group_id'), primary_key=True)
)


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
    # | civicregno      | varchar(25)      | YES  |     | NULL              |                   |
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
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(60))
    firstname = Column(String(255), nullable=False)
    lastname = Column(String(255))
    civicregno = Column(String(25))
    company = Column(String(255))
    orgno = Column(String(12))
    address_street = Column(String(255))
    address_extra = Column(String(255))
    address_zipcode = Column(Integer)
    address_city = Column(String(255))
    address_country = Column(String(2))
    phone = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    member_number = Column(Integer, unique=True)

    groups = relationship('Group',
                          secondary=member_group,
                          back_populates='members')

    def __repr__(self):
        return f'Member(member_id={self.member_id}, member_number={self.member_number}, email={self.email})'


group_permission = Table(
    # mysql> describe membership_group_permissions;
    # +---------------+------------------+------+-----+---------+----------------+
    # | Field         | Type             | Null | Key | Default | Extra          |
    # +---------------+------------------+------+-----+---------+----------------+
    # | id            | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    # | group_id      | int(10) unsigned | NO   | MUL | NULL    |                |
    # | permission_id | int(10) unsigned | NO   | MUL | NULL    |                |
    # +---------------+------------------+------+-----+---------+----------------+
    'membership_group_permissions',
    Base.metadata,
    Column('id', Integer, autoincrement=True, nullable=False, primary_key=True),
    Column('group_id', ForeignKey('membership_groups.group_id'), nullable=False),
    Column('permission_id', ForeignKey('membership_permissions.permission_id'), nullable=False)
)


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
    parent = Column(Integer, index=True, nullable=False, default=0)  # TODO Remove this column.
    left = Column(Integer, index=True, nullable=False, default=0)  # TODO Remove this column.
    right = Column(Integer, index=True, nullable=False, default=0)  # TODO Remove this column.
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    members = relationship('Member',
                           secondary=member_group,
                           back_populates='groups')

    permissions = relationship('Permission',
                               secondary=group_permission,
                               back_populates='groups')
    
    def __repr__(self):
        return f'Group(group_id={self.group_id}, name={self.name})'
  
    
# Calculated property will be a sub executed as a sub select for each groups, since there are not that many groups
# this is fine.
Group.num_members = column_property(
    select([func.count(member_group.columns.member_id)])
    .where(Group.group_id == member_group.columns.group_id)
)


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
    role_id = Column(Integer, nullable=False, server_default=text('0'))  # TODO Remove this column.
    permission = Column(String(255), nullable=False, unique=True)
    group_id = Column(Integer,  nullable=False, server_default=text('0'))  # TODO Remove this column.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)

    groups = relationship('Group',
                          secondary=group_permission,
                          back_populates='permissions')


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
    member_id = Column(Integer, ForeignKey('membership_members.member_id'), nullable=False)
    description = Column(Text)
    tagid = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    member = relationship(Member, backref="keys")


LABACCESS = 'labaccess'
MEMBERSHIP = 'membership'
SPECIAL_LABACESS = 'special_labaccess'


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
    member_id = Column(Integer, ForeignKey('membership_members.member_id'), nullable=False)
    startdate = Column(Date, nullable=False)  # Start date, inclusive
    enddate = Column(Date, nullable=False)    # End date, inclusive
    type = Column(Enum(LABACCESS, MEMBERSHIP, SPECIAL_LABACESS), nullable=False)
    creation_reason = Column(String(255), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    deletion_reason = Column(String(255))  # TODO Unused, remove it?
    
    member = relationship(Member, backref="spans")


# TODO BM Move this somewhere. It is used by core and it should be clear that core is using membership, somewhere where
# membership endpoints are implemented.
def get_member_permissions(member_id=None):
    """ Return query to get all (permission_id, permission) for a memeber. """
    return (
        db_session
            .query(Permission.permission_id, Permission.permission)
            .distinct()
            .join(Group, Permission.groups)
            .join(Member, Group.members)
            .filter_by(member_id=member_id)
    )


# TODO BM Move this somewhere.
def register_permissions(permissions):
    for permission in permissions:
        try:
            db_session.add(Permission(permission=permission))
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
    

# TODO BM Move this somewhere.
def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def hash_password(password):
    bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt())


# TODO BM Move this somewhere, used in core but accesses membership models.
def authenticate(username=None, password=None):
    """ Authenticate a member trough username and password, returns member_id if authenticated. """
    
    member = db_session.query(Member).filter_by(email=username).first()
    
    if not member or not verify_password(password, member.password):
        raise Unauthorized("The username and/or password you specified was incorrect.",
                           fields='username,password', what=BAD_VALUE)
    
    return member.member_id
