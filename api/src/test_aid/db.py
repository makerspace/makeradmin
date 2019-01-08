from random import randint

from faker import Faker


# TODO Reuse obj.py.
from core.models import AccessToken
from membership.models import Member, Group, Permission
from service.api_definition import SERVICE_USER_ID
from service.db import db_session
from test_aid.test_util import random_str


# TODO Use obj.
class DbFactory:
    """ Create entities directly in the db, uses db_session to access the db so it can be used for both remote db
    access and in memory db. """
    
    def __init__(self, test, obj_factory=None):
        self.test = test
        self.obj = obj_factory
        
        self.fake = Faker('sv_SE')
        
        self.access_token = None
        self.member = None
        self.group = None
        self.permission = None

    def create_access_token(self, **kwargs):
        obj = dict(
            user_id=SERVICE_USER_ID,
            access_token=random_str(),
            browser=f'a-browser-{random_str()}',
            ip=f'{randint(0, 255)}.{randint(0, 255)}.{randint(0, 255)}.{randint(0, 255)}',
            expires=self.test.datetime(days=1),
        )
        obj.update(kwargs)
        self.access_token = AccessToken(**obj)
        db_session.add(self.access_token)
        db_session.commit()
        return self.access_token
        
    def create_member(self, **kwargs):
        firstname = self.fake.first_name()
        lastname = self.fake.last_name()
        obj = dict(
            firstname=firstname,
            lastname=lastname,
            password=None,
            member_number=randint(1e8, 9e8),
            address_street=self.fake.street_name(),
            address_extra="N/A",
            address_zipcode=randint(10000, 99999),
            address_city=self.fake.city(),
            address_country=self.fake.country_code(representation="alpha-2"),
            phone=f'070-{randint(1e7, 9e7):07d}',
            civicregno=f"19901011{randint(1000, 9999):04d}",
            email=f'{firstname}.{lastname}+{random_str(6)}@bmail.com'.lower(),
        )
        obj.update(kwargs)
        self.member = Member(**obj)
        db_session.add(self.member)
        db_session.commit()
        return self.member

    def create_group(self, **kwargs):
        obj = dict(
            name=f"group-{random_str(12)}",
            title=self.fake.catch_phrase(),
            description=self.fake.bs(),
        )
        obj.update(kwargs)
        self.group = Group(**obj)
        db_session.add(self.group)
        db_session.commit()
        return self.group

    def create_permission(self, **kwargs):
        obj = dict(
            permission=random_str(),
        )
        obj.update(kwargs)
        self.permission = Permission(**obj)
        db_session.add(self.permission)
        db_session.commit()
        return self.permission
