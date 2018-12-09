import os
from datetime import datetime, timedelta

from unittest import TestCase

import stripe

from library.obj import ObjFactory
from library.util import get_env

stripe.api_key = get_env("STRIPE_PUBLIC_KEY")
test_mode = os.environ.get('TEST_MODE', 'DEV')


class TestCaseBase(TestCase):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.obj = ObjFactory()
        
        if test_mode == 'DEV':
            self.admin_url = 'http://localhost:8009'
            self.public_url = 'http://localhost:8011'
            self.api_url = 'http://localhost:8010'
            
        elif test_mode == 'DOCKER':
            self.admin_url = 'http://admin:80'
            self.public_url = 'http://public:80'
            self.api_url = 'http://api-gateway:80'
            
        else:
            raise Exception(f"unknown test_mode {test_mode}")

        self.now = datetime.now()
        self.today = self.now.date()
        
    def date(self, days=0):
        return self.today + timedelta(days=days)
