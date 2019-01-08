from datetime import datetime, timedelta
from unittest import TestCase

from flask import Flask
from sqlalchemy import create_engine

from test_aid.db import DbFactory
from service.db import db_session_factory
from service.internal_service import InternalService


# TODO The systest and unittests have overlap, perhaps move systests to api when all service are converted?
class TestCaseBase(TestCase):
    """ Includes setup of flask and in memory db, if not wanted subclass unittest.TestCase directly. """
    
    models = []
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.app = Flask(__name__)

        engine = create_engine('sqlite:///:memory:')
        for model in self.models:
            model.Base.metadata.create_all(engine)
        
        db_session_factory.init_with_engine(engine)

        self.service = InternalService('service')

        self.now = datetime.now()
        self.today = self.now.date()
        
    def setUp(self):
        self.db = DbFactory(self)
        
    def date(self, days=0):
        return self.today + timedelta(days=days)

    def datetime(self, **kwargs):
        return self.now + timedelta(**kwargs)

