import time
from copy import copy
from datetime import date, datetime, timedelta, timezone
from unittest import TestCase

from flask import Flask
from membership.member_auth import hash_password
from service.db import db_session, db_session_factory
from service.internal_service import InternalService
from shop.stripe_setup import are_stripe_keys_live, are_stripe_keys_set, setup_stripe
from sqlalchemy import Numeric, create_engine

from test_aid.db import DbFactory
from test_aid.obj import DEFAULT_PASSWORD, ObjFactory
from test_aid.test_util import classinstancemethod


class TestBase(TestCase):
    """Base test with obj factory and date helpers."""

    now: datetime
    today: date
    obj: ObjFactory

    @classmethod
    def setUpClass(self) -> None:
        super().setUpClass()
        self.obj = ObjFactory(self)

        self.now = datetime.now(timezone.utc)
        self.today = self.now.date()

    @classinstancemethod
    def date(self, days: int = 0) -> date:
        return self.today + timedelta(days=days)

    @classinstancemethod
    def datetime(self, **kwargs) -> datetime:
        return self.now + timedelta(**kwargs)

    def this_test_failed(self):
        if hasattr(self._outcome, "errors"):
            # Python 3.4 - 3.10  (These two methods have no side effects)
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            # Python 3.11+
            # This does not work when running in pytest, will fix later, maybe....
            result = self._outcome.result

        return getattr(result, "errors", None) or getattr(result, "failures", None)


class FlaskTestBase(TestBase):
    """Includes setup of flask and in memory db."""

    models = []
    app: Flask
    db: DbFactory
    service: InternalService

    @classmethod
    def setUpClass(self) -> None:
        super().setUpClass()

        self.app = Flask(__name__)

        # Make sure sessions is removed so it is not using another engine in this thread.
        db_session.remove()

        engine = create_engine("sqlite:///:memory:")
        for model in self.models:
            metadata = model.Base.metadata
            for table in metadata.tables.values():
                for column in table.columns.values():
                    if isinstance(column.type, Numeric):
                        column.type.asdecimal = False
            metadata.create_all(engine)

        db_session_factory.init_with_engine(engine)

        self.service = InternalService("service")

        self.db = DbFactory(self, self.obj)

        if are_stripe_keys_set():
            if are_stripe_keys_live():
                raise Exception(
                    "Live Stripe keys detected during test setup. Using live keys in tests is prohibited to prevent unintended side effects."
                )
            setup_stripe(private=True)


class ShopTestMixin:
    """Mixin that sets up data for shop tests."""

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
        return {"number": str(number), "exp_month": 12, "exp_year": 2030, "cvc": "123"}

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.factory = self.api if hasattr(self, "api") else self.db
        self.category = self.factory.create_category()

        for i, product_kwargs in enumerate(self.products):
            product_kwargs = copy(product_kwargs)
            action_kwargs = product_kwargs.pop("action", None)
            product = self.factory.create_product(**product_kwargs)
            product_id = int(product.id if hasattr(product, "id") else product["id"])
            product_price = float(product.price if hasattr(product, "price") else product["price"])
            if action_kwargs:
                self.factory.create_product_action(product_id=product_id, **action_kwargs)
            setattr(self, f"p{i}", product)
            setattr(self, f"p{i}_id", product_id)
            setattr(self, f"p{i}_price", product_price)

    @classmethod
    def tearDownClass(self):
        for i in range(len(self.products)):
            self.factory.delete_product(getattr(self, f"p{i}_id"))
        self.factory.delete_category()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.member = self.factory.create_member(password=hash_password(DEFAULT_PASSWORD))
        self.member_id = self.member.member_id if hasattr(self.member, "member_id") else self.member["member_id"]

        self.test_start_timestamp = str(int(time.time()))
