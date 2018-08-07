from factory import Sequence, Factory, Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from multi_access import models
from multi_access.maker_admin import MakerAdminMember
from test.db_base import Session


class AuthorityFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Authority
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = 'flush'
      
    id = Sequence(lambda n: n + 1)
    name = Sequence(lambda n: f"stockholm makerspace {n}")
    flags = 0


class CustomerFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.Customer
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = 'flush'
      
    id = Sequence(lambda n: n + 1)
    name = Sequence(lambda n: f"stockholm makerspace {n}")


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = models.User
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = 'flush'
    
    name = Sequence(lambda n: str(1001 + n))
    card = Sequence(lambda n: str(100000000001 + n))
    customer = SubFactory(CustomerFactory)
    blocked = False
    

class MakerAdminMemberFactory(Factory):
    class Meta:
        model = MakerAdminMember
        
    member_number = Sequence(lambda n: n + 1001)
    firstname = Faker('first_name')
    lastname = Faker('last_name')
    rfid_tag = Sequence(lambda n: str(100000000001 + n))
    end_timestamp = Faker('future_datetime')
