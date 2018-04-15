from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    
    __tablename__ = 'Users'
    
    id = Column("Id", Integer(), primary_key=True, autoincrement=True)
    
    name = Column("Name", String(length=50, collation="Finnish_Swedish_CI_AI"), nullable=False, index=True)
    customer_id = Column("customerId", Integer(), index=True)
    stop_timestamp = Column("Stop", DateTime(timezone=False))
    