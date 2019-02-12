from sqlalchemy import Column, Integer, String, DateTime, Text, Date, Enum, Table, ForeignKey, func, text, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, column_property

Base = declarative_base()


member_group = Table(
    'membership_members_groups',
    Base.metadata,
    Column('member_id', ForeignKey('membership_members.member_id'), primary_key=True),
    Column('group_id', ForeignKey('membership_groups.group_id'), primary_key=True)
)


class Member(Base):
    
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
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    member_number = Column(Integer, unique=True)

    groups = relationship('Group',
                          secondary=member_group,
                          back_populates='members')

    def __repr__(self):
        return f'Member(member_id={self.member_id}, member_number={self.member_number}, email={self.email})'


group_permission = Table(
    'membership_group_permissions',
    Base.metadata,
    Column('id', Integer, autoincrement=True, nullable=False, primary_key=True),
    Column('group_id', ForeignKey('membership_groups.group_id'), nullable=False),
    Column('permission_id', ForeignKey('membership_permissions.permission_id'), nullable=False)
)


class Group(Base):
    
    __tablename__ = 'membership_groups'
    
    group_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    
    members = relationship('Member',
                           secondary=member_group,
                           lazy='dynamic',
                           back_populates='groups')

    permissions = relationship('Permission',
                               secondary=group_permission,
                               back_populates='groups')
    
    def __repr__(self):
        return f'Group(group_id={self.group_id}, name={self.name})'
  
    
# Calculated property will be executed as a sub select for each groups, since it is not that many groups this will be
# fine.
Group.num_members = column_property(
    select([func.count(member_group.columns.member_id)])
    .where(Group.group_id == member_group.columns.group_id)
)


class Permission(Base):
    __tablename__ = 'membership_permissions'

    permission_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    permission = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    groups = relationship('Group',
                          secondary=group_permission,
                          back_populates='permissions')


class Key(Base):

    __tablename__ = 'membership_keys'

    key_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey('membership_members.member_id'), nullable=False)
    description = Column(Text)
    tagid = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    
    member = relationship(Member, backref="keys")


LABACCESS = 'labaccess'
MEMBERSHIP = 'membership'
SPECIAL_LABACESS = 'special_labaccess'


class Span(Base):

    __tablename__ = 'membership_spans'

    span_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey('membership_members.member_id'), nullable=False)
    startdate = Column(Date, nullable=False)  # Start date, inclusive
    enddate = Column(Date, nullable=False)    # End date, inclusive
    type = Column(Enum(LABACCESS, MEMBERSHIP, SPECIAL_LABACESS), nullable=False)
    creation_reason = Column(String(255), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    deletion_reason = Column(String(255))
    
    member = relationship(Member, backref="spans")
