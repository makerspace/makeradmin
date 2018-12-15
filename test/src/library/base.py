from datetime import datetime, timedelta

from unittest import TestCase

import stripe

from library.obj import ObjFactory
from library.test_config import STRIPE_PUBLIC_KEY, HOST_FRONTEND, HOST_PUBLIC, HOST_BACKEND

stripe.api_key = STRIPE_PUBLIC_KEY

VALID_NON_3DS_CARD_NO = "378282246310005"

EXPIRES_CVC_ZIP = "4242424242424"


class TestCaseBase(TestCase):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.obj = ObjFactory()
        
        self.admin_url = HOST_FRONTEND
        self.public_url = HOST_PUBLIC
        self.api_url = HOST_BACKEND

        self.now = datetime.now()
        self.today = self.now.date()
        
    def date(self, days=0):
        return self.today + timedelta(days=days)

    def this_test_failed(self):
        result = self.defaultTestResult()
        self._feedErrorsToResult(result, self._outcome.errors)
        return result.errors or result.failures

