from random import randint

from faker import Faker

from aid.systest.util import random_str

DEFAULT_PASSWORD = '1q2w3e'
DEFAULT_PASSWORD_HASH = "$2y$10$NcNoheVsKVo2Agz3FLeI8.fhAgbmRV/NoJMqPC67ZXiqgqfE5DE.S"

ADD_MEMBERSHIP_DAYS = 1
ADD_LABACCESS_DAYS = 2


class ObjFactory:
    """ Create dicts representing entities. """
    
    def __init__(self):
        self.fake = Faker('sv_SE')
        
        self.member = None
        self.group = None
        self.category = None
        self.product = None
        self.action = None
    
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
        self.member = obj
        return self.member
        
    def create_group(self, **kwargs):
        obj = dict(
            name=f"group-{random_str(12)}",
            title=self.fake.catch_phrase(),
            description=self.fake.bs(),
        )
        obj.update(kwargs)
        self.group = obj
        return self.group

    def create_category(self, **kwargs):
        obj = dict(
            name=f"category-{random_str(12)}",
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
            action_id=ADD_MEMBERSHIP_DAYS,
            value=365,
        )
        obj.update(**kwargs)
        self.action = obj
        return self.action
