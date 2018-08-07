from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from multi_access.models import Base, User, AuthorityInUser, Authority, Customer
from test.base import BaseTest

engine = create_engine('sqlite://')
Session = scoped_session(sessionmaker(bind=engine))

Base.metadata.create_all(engine)


class DbBaseTest(BaseTest):
    
    def setUp(self):
        super().setUp()
        self.session = Session()
        self.session.query(User).delete()
        self.session.query(AuthorityInUser).delete()
        self.session.query(Authority).delete()
        self.session.query(Customer).delete()
        self.session.commit()
    
    def tearDown(self):
        self.session.rollback()
        Session.remove()
        super().tearDown()
        
