from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from destroyer.models import Base
from test.base import BaseTest

engine = create_engine('sqlite://')
Session = scoped_session(sessionmaker(bind=engine))

Base.metadata.create_all(engine)


class DbBaseTest(BaseTest):
    
    def setUp(self):
        super().setUp()
        self.session = Session()
    
    def tearDown(self):
        self.session.rollback()
        Session.remove()
        super().tearDown()
        
