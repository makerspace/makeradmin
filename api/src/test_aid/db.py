import random
from datetime import datetime
from random import randint
from faker import Faker


from core.models import AccessToken, PasswordResetToken
from core.service_users import TEST_SERVICE_USER_ID
from membership.models import Member, Group, Permission, Span, Key, Box, PhoneNumberChangeRequest
from messages.models import Message
from service.db import db_session
from shop.models import ProductCategory, Product, ProductAction
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
        self.key = None
        self.permission = None
        self.message = None
        self.box = None
        self.category = None
        self.product = None
        self.action = None
        self.password_reset_token = None
        self.phone_request = None
        
    def create_access_token(self, **kwargs):
        obj = dict(
            user_id=TEST_SERVICE_USER_ID,
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

    def create_phone_request(self, **kwargs):
        obj = self.obj.create_phone_request(**kwargs)
        self.phone_request = PhoneNumberChangeRequest(**obj, member=self.member)
        db_session.add(self.phone_request)
        db_session.commit()
        return self.phone_request

    def create_box(self, **kwargs):
        obj = dict(
            member_id=self.member.member_id,
            box_label_id=randint(int(1e9), int(9e9)),
            session_token=random_str(),
        )
        obj.update(kwargs)
        self.box = Box(**obj)
        db_session.add(self.box)
        db_session.commit()
        return self.box

    def create_group(self, **kwargs):
        obj = self.obj.create_group(**kwargs)
        self.group = Group(**obj)
        db_session.add(self.group)
        db_session.commit()
        return self.group

    def create_span(self, **kwargs):
        if 'member' in kwargs:
            member = kwargs.pop('member')
        else:
            member = self.member
            
        obj = self.obj.create_span(**kwargs)
        self.span = Span(**obj, member=member)
        db_session.add(self.span)
        db_session.commit()
        return self.span

    def create_key(self, **kwargs):
        if 'member' in kwargs:
            member = kwargs.pop('member')
        else:
            member = self.member

        obj = self.obj.create_key(**kwargs)
        self.key = Key(**obj, member=member)
        db_session.add(self.key)
        db_session.commit()
        return self.key

    def create_message(self, member=None, **kwargs):
        member = member or self.member
        
        obj = dict(
            member=member,
            subject=random_str(),
            body=self.fake.bs(),
            recipient=member.email if member else self.fake.email(),
            status=Message.QUEUED,
        )
        obj.update(**kwargs)
        self.message = Message(**obj)
        db_session.add(self.message)
        db_session.commit()
        return self.member

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
        while True:
            member_number = randint(5000, 2000000)
            sql = "SELECT 1 FROM membership_members WHERE member_number = :number"
            if db_session.execute(sql, params=dict(number=member_number)).first() is None:
                break
        return member_number

    def create_category(self, **kwargs):
        obj = self.obj.create_category(**kwargs)
        self.category = ProductCategory(**obj)
        db_session.add(self.category)
        db_session.commit()
        return self.category

    def delete_category(self, id=None):
        category_id = id or self.category.id
        db_session.query(ProductCategory).filter(ProductCategory.id == category_id).delete()
        db_session.flush()

    def create_product(self, **kwargs):
        if self.category:
            kwargs.setdefault('category_id', self.category.id)

        obj = self.obj.create_product(**kwargs)

        self.product = Product(**obj)
        db_session.add(self.product)
        db_session.flush()
        return self.product

    def delete_product(self, id=None):
        product_id = id or self.product.id
        db_session.query(ProductAction).filter(ProductAction.product_id == product_id).delete()
        db_session.query(Product).filter(Product.id == product_id).delete()
        db_session.flush()

    def create_product_action(self, **kwargs):
        if self.product:
            kwargs.setdefault('product_id', self.product.id)

        obj = self.obj.create_product_action(**kwargs)
        self.action = ProductAction(**obj)
        db_session.add(self.action)
        db_session.flush()
        return self.action

    def create_password_reset_token(self, member=None, **kwargs):
        member = member or self.member
        
        obj = dict(
            member_id=member.member_id,
            token=random_str(),
        )
        obj.update(**kwargs)
        self.password_reset_token = PasswordResetToken(**obj)
        db_session.add(self.password_reset_token)
        db_session.commit()
        return self.password_reset_token
