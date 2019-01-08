from random import randint
from faker import Faker


from core.models import AccessToken
from membership.models import Member, Group, Permission
from service.api_definition import SERVICE_USER_ID
from service.db import db_session
from test_aid.test_util import random_str


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
        obj = self.obj.create_member(**kwargs)
        self.member = Member(**obj)
        db_session.add(self.member)
        db_session.commit()
        return self.member

    def create_group(self, **kwargs):
        obj = self.obj.create_group(**kwargs)
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
