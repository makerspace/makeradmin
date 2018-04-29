from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from multi_access import models
from test.db_base import Session


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
    
    name = Sequence(lambda n: str(n))
    card = Sequence(lambda n: str(10000 + n))

