import os
from random import choice, seed
from string import ascii_letters, digits

from factory import Faker, Factory, LazyAttribute, Sequence, LazyFunction
from factory.fuzzy import FuzzyText


seed(os.urandom(8))


def random_str(length=12):
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


class MemberFactory(Factory):
    class Meta:
        model = dict
    
    firstname = Faker('first_name')
    lastname = Faker('last_name')
    password = LazyFunction(lambda: "$2y$10$NcNoheVsKVo2Agz3FLeI8.fhAgbmRV/NoJMqPC67ZXiqgqfE5DE.S")
    address_street = Faker('street_name')
    address_extra = LazyFunction(lambda: "N/A")
    address_zipcode = Sequence(lambda n: 10200 + n)
    address_city = Faker('city')
    address_country = Faker('country_code', representation="alpha-2")
    phone = Sequence(lambda n: f'070-{n:07d}')
    civicregno = Sequence(lambda n: f"19901011{9944 + n:04d}")
    email = LazyAttribute(lambda o: f'{o.firstname}.{o.lastname}+{random_str(6)}@bmail.com'.lower())


class GroupFactory(Factory):
    class Meta:
        model = dict
    
    name = FuzzyText(length=12, chars=ascii_letters, prefix='group-')
    title = Faker('catch_phrase')
    description = Faker('bs')
