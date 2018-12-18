import sys
from copy import copy
from datetime import datetime, timedelta

from unittest import TestCase, skipIf

import stripe

from library.obj import ObjFactory, DEFAULT_PASSWORD_HASH
from library.test_config import STRIPE_PUBLIC_KEY, HOST_FRONTEND, HOST_PUBLIC, HOST_BACKEND

stripe.api_key = STRIPE_PUBLIC_KEY

VALID_NON_3DS_CARD_NO = "378282246310005"
EXPIRED_3DS_CARD_NO = "4000000000000069"

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


class ShopTestMixin:

    products = []
    
    p0 = None
    p0_id = None
    p0_price = None

    p1 = None
    p1_id = None
    p1_price = None

    p2 = None
    p2_id = None
    p2_price = None

    @staticmethod
    def card(number):
        return {
            "number": str(number),
            "exp_month": 12,
            "exp_year": 2030,
            "cvc": '123'
        }

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.category = self.api.create_category()
        
        for i, product_kwargs in enumerate(self.products):
            product_kwargs = copy(product_kwargs)
            action_kwargs = product_kwargs.pop('action', None)
            product = self.api.create_product(**product_kwargs)
            product_id = int(product['id'])
            product_price = float(product['price'])
            if action_kwargs:
                self.api.create_product_action(product_id=product_id, **action_kwargs)
            setattr(self, f'p{i}', product)
            setattr(self, f'p{i}_id', product_id)
            setattr(self, f'p{i}_price', product_price)

    @classmethod
    def tearDownClass(self):
        for i in range(len(self.products)):
            self.api.delete_product(getattr(self, f'p{i}_id'))
        self.api.delete_category()
        super().tearDownClass()

    @skipIf(not stripe.api_key, "webshop tests require stripe api key in .env file")
    def setUp(self):
        super().setUp()
        self.member = self.api.create_member(password=DEFAULT_PASSWORD_HASH)
        self.member_id = self.member['member_id']
        self.token = self.api.login_member()
