import string
from functools import partial
from random import choice

from factory import Sequence, Factory, LazyFunction, Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from multi_access import models
from multi_access.maker_admin import MakerAdminMember
from test.db_base import Session


# TODO Possible to use hypotesis for random generation?
def uniqueid(length=12):
    return ''.join(choice(string.ascii_letters + string.digits + "_-") for _ in range(length))


class CustomerFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Customer
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = 'flush'

    name = Sequence(lambda n: f"customer-{n}")


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.User
        sqlalchemy_session = Session
    
    name = Sequence(lambda n: str(1001 + n))
    card = Sequence(lambda n: str(100000000001 + n))
    customer = SubFactory(CustomerFactory)
    

class MakerAdminMemberFactory(Factory):
    class Meta:
        model = MakerAdminMember
        
    member_id = Sequence(lambda n: n + 1)
    member_number = Sequence(lambda n: n + 1001)
    firstname = Faker('first_name')
    lastname = Faker('last_name')
    key_id = Sequence(lambda n: n)
    rfid_tag = LazyFunction(partial(uniqueid, length=12))
    status = False
    end_timestamp = Faker('future_datetime')
