from random import randint

from faker import Faker

from library.util import random_str

DEFAULT_PASSWORD = '1q2w3e'
DEFAULT_PASSWORD_HASH = "$2y$10$NcNoheVsKVo2Agz3FLeI8.fhAgbmRV/NoJMqPC67ZXiqgqfE5DE.S"


# class MemberFactory(Factory):
#     class Meta:
#         model = dict
#
#     firstname = Faker('first_name')
#     lastname = Faker('last_name')
#     password = LazyFunction(lambda: "$2y$10$NcNoheVsKVo2Agz3FLeI8.fhAgbmRV/NoJMqPC67ZXiqgqfE5DE.S")  # 1q2w3e
#     address_street = Faker('street_name')
#     address_extra = LazyFunction(lambda: "N/A")
#     address_zipcode = Sequence(lambda n: 10200 + n)
#     address_city = Faker('city')
#     address_country = Faker('country_code', representation="alpha-2")
#     phone = Sequence(lambda n: f'070-{n:07d}')
#     civicregno = Sequence(lambda n: f"19901011{9944 + n:04d}")
#     email = LazyAttribute(lambda o: f'{o.firstname}.{o.lastname}+{random_str(6)}@bmail.com'.lower())
#
#
# class GroupFactory(Factory):
#     class Meta:
#         model = dict
#
#     name = FuzzyText(length=12, chars=ascii_letters, prefix='group-')
#     title = Faker('catch_phrase')
#     description = Faker('bs')
#
#
# class CategoryFactory(Factory):
#     class Meta:
#         model = dict
#
#     name = FuzzyText(length=12, chars=ascii_letters, prefix='category-')
#
#
# class ProductFactory(Factory):
#     class Meta:
#         model = dict
#
#     name = FuzzyText(length=12, chars=ascii_letters, prefix='product-')
#     price = LazyFunction(lambda: 100.0)
#     description = Faker('bs')
#     unit = LazyFunction(lambda: "st")
#     smallest_multiple = LazyFunction(lambda: 1)
#     filter = LazyFunction(lambda: None)
#     category_id = LazyFunction(lambda: None)


class ObjFactory:
    """ Create dicts representing entities. """
    
    def __init__(self):
        self.fake = Faker('sv_SE')
        
        self.member = None
    
    def create_member(self, **kwargs):
        firstname = self.fake.first_name()
        lastname = self.fake.last_name()
        obj = dict(
            firstname=firstname,
            lastname=lastname,
            password=DEFAULT_PASSWORD_HASH,
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
        
    def create_group(self, **kwarg):
        pass

    def create_cagetory(self, **kwarg):
        pass

    def create_product(self, **kwarg):
        pass
