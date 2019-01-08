from datetime import datetime, timedelta
from unittest import TestCase

from flask import Flask
from sqlalchemy import create_engine

from service.db import db_session_factory
from service.internal_service import InternalService
from test_aid.db import DbFactory
from test_aid.obj import ObjFactory
from test_aid.test_util import classinstancemethod


class TestBase(TestCase):
    """ Base test with obj factory and date helpers. """
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.obj = ObjFactory()
        
        self.now = datetime.now()
        self.today = self.now.date()
        
    @classinstancemethod
    def date(self, days=0):
        return self.today + timedelta(days=days)

    @classinstancemethod
    def datetime(self, **kwargs):
        return self.now + timedelta(**kwargs)
    
    def this_test_failed(self):
        result = self.defaultTestResult()
        self._feedErrorsToResult(result, self._outcome.errors)
        return result.errors or result.failures
    

class FlaskTestBase(TestBase):
    """ Includes setup of flask and in memory db. """
    
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

        self.db = DbFactory(self, self.obj)
