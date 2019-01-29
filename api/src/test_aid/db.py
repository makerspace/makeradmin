from random import randint
from faker import Faker


from core.models import AccessToken
from membership.models import Member, Group, Permission, Span
from messages.models import Message, Recipient
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
        self.span = None
        self.permission = None
        self.message = None
        self.recipient = None

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
        self.member = Member(**obj, member_number=self.get_member_number())
        db_session.add(self.member)
        db_session.commit()
        return self.member

    def create_group(self, **kwargs):
        obj = self.obj.create_group(**kwargs)
        self.group = Group(**obj)
        db_session.add(self.group)
        db_session.commit()
        return self.group

    def create_span(self, **kwargs):
        member = kwargs.get('member') or self.member
        obj = self.obj.create_span(**kwargs)
        self.span = Span(**obj, member=member)
        db_session.add(self.span)
        db_session.commit()
        return self.span

    def create_message(self, **kwargs):
        obj = self.obj.create_message(**kwargs)
        self.message = Message(**obj)
        db_session.add(self.message)
        db_session.commit()
        return self.message

    def create_recipient(self, **kwargs):
        obj = dict(
            title=random_str(),
            description=self.fake.bs(),
            recipient=self.fake.email(),
            date_sent=self.test.date(),
            status='sent',
        )
        obj.update(**kwargs)
        self.recipient = Recipient(**obj)
        db_session.add(self.recipient)
        db_session.commit()
        return self.recipient

    def create_permission(self, **kwargs):
        obj = dict(
            permission=random_str(),
        )
        obj.update(kwargs)
        self.permission = Permission(**obj)
        db_session.add(self.permission)
        db_session.commit()
        return self.permission

    def get_member_number(self):
        # Ugly but will work most of the time.
        sql = "SELECT COALESCE(MAX(member_number), 0) FROM membership_members"
        member_number = db_session.execute(sql).fetchone()[0] + randint(1000, 2000)
        return member_number
        
        