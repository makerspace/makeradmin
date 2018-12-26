from typing import Union

from sqlalchemy.orm import scoped_session, Session, sessionmaker


class SessionFactoryWrapper:
    
    def __init__(self):
        self.session_factory = None
        
    def init_with_engine(self, engine):
        self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
    def __call__(self, *args, **kwargs):
        return self.session_factory(*args, **kwargs)
        

db_session_factory = SessionFactoryWrapper()

db_session: Union[Session, scoped_session] = scoped_session(db_session_factory)
