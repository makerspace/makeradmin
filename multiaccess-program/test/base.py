from datetime import timedelta, datetime
from unittest import TestCase
from multi_access.util import classinstancemethod, utc


class BaseTest(TestCase):
    
    def setUp(self):
        super().setUp()
        self.now = datetime.utcnow()
        
    @classinstancemethod
    def datetime(self, **kwargs):
        return self.now + timedelta(**kwargs)
    
