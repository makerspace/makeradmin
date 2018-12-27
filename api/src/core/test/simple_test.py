from datetime import datetime
from unittest import TestCase

from flask import Flask
from sqlalchemy import create_engine

import core
from core import models
from core.models import AccessToken
from service.db import db_session_factory, db_session


class Test(TestCase):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.app = Flask(__name__)
        self.app.testing = True
        self.app.register_blueprint(core.service, url_prefix='')
        self.client = self.app.test_client()
        
        engine = create_engine('sqlite:///:memory:')
        models.Base.metadata.create_all(engine)
        
        db_session_factory.init_with_engine(engine)
        
    def test(self):
        db_session.add(AccessToken(user_id=1, access_token='23dd', browser='', ip='', expires=datetime.utcnow()))
        db_session.commit()
        self.assertEqual('login-23dd', self.client.get('/oauth/token').data.decode())
