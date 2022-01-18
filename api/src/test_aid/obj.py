from random import randint, choice

from faker import Faker

from membership.models import Span
from messages.models import Message
from shop.models import ProductAction
from test_aid.test_util import random_str
import re

DEFAULT_PASSWORD = 'D9ub8$13'


class ObjFactory:
    """ Create dicts representing entities. """
    
    def __init__(self, test):
        self.test = test
        self.fake = Faker('sv_SE')
        
        self.member = None
        self.member_storage = None
        self.nag = None
        self.group = None
        self.category = None
        self.product = None
        self.action = None
        self.key = None
        self.span = None
        self.message = None
    
    def create_member(self, **kwargs):
        firstname = self.fake.first_name()
        lastname = self.fake.last_name()
        obj = dict(
            firstname=firstname,
            lastname=lastname,
            password=None,
            address_street=self.fake.street_name(),
            address_extra="N/A",
            address_zipcode=randint(10000, 99999),
            address_city=self.fake.city(),
            address_country=self.fake.country_code(representation="alpha-2"),
            phone=f'070-{randint(1e7, 9e7):07d}',
            civicregno=f"19901011{randint(1000, 9999):04d}",
            email=re.sub('[^a-zA-Z0-9.!#$%&\'*+\\/=?^_`{|}~\\-@\\.]', '_',
                         f'{firstname}.{lastname}+{random_str(6)}@bmail.com'.lower().replace(' ', '_')),
        )
        obj.update(kwargs)
        self.member = obj
        return self.member

    def create_member_storage(self, storage_type, **kwargs):
        obj = dict(
            member_id=self.member.member_id,
            label_id=randint(1e9, 9e9),
            fixed_end_date='2029-01-01',
            storage_type=storage_type,
        )
        obj.update(kwargs)
        self.member_storage = obj
        return self.member_storage

    def create_storage_nag(self, nag_type, **kwargs):
        obj = dict(
            member_id=self.member.member_id,
            label_id=randint(1e9, 9e9),
            nag_at=self.test.date(),
            nag_type=nag_type,
        )
        obj.update(kwargs)
        self.nag = obj
        return self.nag

    def create_group(self, **kwargs):
        obj = dict(
            name=f"group-{random_str(12)}",
            title=f"group-title-{random_str(12)}",
            description=self.fake.bs(),
        )
        obj.update(kwargs)
        self.group = obj
        return self.group

    def create_key(self, **kwargs):
        obj = dict(
            tagid=str(randint(1e12, 9e12)),
            description=self.fake.bs(),
        )
        obj.update(kwargs)
        self.key = obj
        return self.key

    def create_span(self, **kwargs):
        obj = dict(
            startdate=self.test.date(days=-randint(40, 60)),
            enddate=self.test.date(days=-randint(10, 30)),
            type=choice((Span.LABACCESS, Span.MEMBERSHIP, Span.SPECIAL_LABACESS)),
            creation_reason=random_str(),
        )
        obj.update(kwargs)
        self.span = obj
        return self.span
    
    def create_category(self, **kwargs):
        obj = dict(
            name=f"category-{random_str(12)}",
            display_order=randint(1e8, 9e8),
        )
        obj.update(kwargs)
        self.category = obj
        return self.category

    def create_product(self, **kwargs):
        category_id = kwargs.pop('category_id', None) or (self.category and self.category['id'])
        obj = dict(
            name=f"product-{random_str(12)}",
            price=100.0,
            description=self.fake.bs(),
            unit="st",
            display_order=randint(1e8, 9e8),
            smallest_multiple=1,
            filter=None,
            category_id=category_id,
        )
        obj.update(kwargs)
        self.product = obj
        return self.product

    def create_product_action(self, **kwargs):
        obj = dict(
            product_id=0,
            action_type=ProductAction.ADD_MEMBERSHIP_DAYS,
            value=365,
        )
        obj.update(**kwargs)
        self.action = obj
        return self.action

    def create_message(self, **kwargs):
        obj = dict(
            subject=random_str(),
            body=self.fake.bs(),
            recipient=self.fake.email(),
            status=Message.QUEUED,
        )
        obj.update(**kwargs)
        self.message = obj
        return self.message
