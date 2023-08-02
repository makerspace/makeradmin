from datetime import datetime
from random import randint, choice, seed
from typing import Any, Dict
from faker import Faker
from membership.enums import PriceLevel

from membership.models import Member, Span
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
        self.group = None
        self.category = None
        self.product = None
        self.action = None
        self.key = None
        self.span = None
        self.message = None
        self.phone_request = None
        seed()

    def create_member(self, **kwargs) -> Dict[str, Any]:
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
            phone=random_phone_number(),
            civicregno=f"19901011{randint(1000, 9999):04d}",
            email=re.sub('[^a-zA-Z0-9.!#$%&\'*+\\/=?^_`{|}~\\-@\\.]', '_',
                         f'{firstname}.{lastname}+{random_str(6)}@bmail.com'.lower().replace(' ', '_')),
            price_level=PriceLevel.Normal.value,
            price_level_motivation=None,
        )
        obj.update(kwargs)
        self.member = obj
        return self.member

    def create_phone_request(self, **kwargs):
        obj = dict(
            phone=random_phone_number(),
            validation_code=randint(1, 999999),
            completed=False,
            timestamp=datetime.now(),
        )
        obj.update(kwargs)
        self.phone_request = obj
        return self.phone_request
        
    def create_group(self, **kwargs):
        obj = dict(
            name=f"group-{random_str(12)}",
            title=f"group-title-{random_str(12)}",
            description=self.fake.bs(),
        )
        obj.update(kwargs)
        self.group = obj
        return self.group

    def create_key(self, **kwargs) -> Dict[str,str]:
        obj = dict(
            tagid=str(randint(int(1e12), int(9e12))),
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
            display_order=randint(int(1e8), int(9e8)),
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
            display_order=randint(int(1e8), int(9e8)),
            smallest_multiple=1,
            filter=None,
            category_id=category_id,
            product_metadata=dict()
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


def random_phone_number() -> str:
    return f'070-1{randint(int(1e6), int(9e6)):06d}'