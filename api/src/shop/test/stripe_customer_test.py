from logging import getLogger
from typing import Any, Dict, List
from unittest import skipIf

import core.models
import membership.models
import messages.models
import shop.models
import stripe
from membership.models import Member
from shop.stripe_constants import (
    MakerspaceMetadataKeys as MSMetaKeys,
)
from shop.stripe_customer import (
    _get_metadata_for_stripe_customer,
    delete_stripe_customer,
    eq_makeradmin_stripe_customer,
    get_and_sync_stripe_customer,
    get_or_create_stripe_customer,
    update_stripe_customer,
)
from shop.stripe_util import are_metadata_dicts_equivalent, retry
from test_aid.systest_config import STRIPE_PRIVATE_KEY
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


class StripeCustomerTest(ShopTestMixin, FlaskTestBase):
    # Some of the tests here will generate new customers in stripe, but they will be marked as deleted.
    # You can clear the test area in stripe's developer dashboard.

    models = [membership.models, messages.models, shop.models, core.models]

    @skipIf(True, "stripe customer tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_members: List[Member] = []

    def tearDown(self) -> None:
        for makeradmin_member in self.seen_members:
            delete_stripe_customer(makeradmin_member.member_id)
            return super().tearDown()

    @staticmethod
    def assert_customer(makeradmin_member: Member, stripe_test_customer: stripe.Customer) -> None:
        assert stripe_test_customer
        assert stripe_test_customer.email == makeradmin_member.email.strip()
        expected_metadata = _get_metadata_for_stripe_customer(makeradmin_member)
        assert are_metadata_dicts_equivalent(stripe_test_customer.metadata, expected_metadata)
        assert makeradmin_member.stripe_customer_id == stripe_test_customer.id

    def test_create_customer_without_pending(self) -> None:
        makeradmin_test_member = self.db.create_member(
            firstname="customer",
            lastname="test",
            email="test@makerspace.se",
            pending_activation=False,
        )
        self.seen_members.append(makeradmin_test_member)
        stripe_test_customer = get_or_create_stripe_customer(makeradmin_test_member)
        self.assert_customer(makeradmin_test_member, stripe_test_customer)

    def test_create_customer_with_pending(self) -> None:
        makeradmin_test_member = self.db.create_member(
            firstname="customer",
            lastname="test",
            email="test@makerspace.se",
            pending_activation=True,
        )
        self.seen_members.append(makeradmin_test_member)
        stripe_test_customer = get_or_create_stripe_customer(makeradmin_test_member)
        self.assert_customer(makeradmin_test_member, stripe_test_customer)

    def test_delete_customer(self) -> None:
        makeradmin_test_member = self.db.create_member(
            firstname="customer",
            lastname="test",
            email="test@makerspace.se",
        )
        stripe_test_customer = get_or_create_stripe_customer(makeradmin_test_member)
        delete_stripe_customer(makeradmin_test_member.member_id)
        assert makeradmin_test_member.stripe_customer_id is None
        deleted_customer = retry(lambda: stripe.Customer.retrieve(stripe_test_customer.id))
        assert deleted_customer.deleted

    def test_update_customer(self) -> None:
        makeradmin_test_member = self.db.create_member(
            firstname="customer",
            lastname="test",
            email="test@makerspace.se",
        )
        self.seen_members.append(makeradmin_test_member)
        get_or_create_stripe_customer(makeradmin_test_member)
        makeradmin_test_member.email = "new_email@makerspace.se"
        stripe_test_customer = update_stripe_customer(makeradmin_test_member)
        self.assert_customer(makeradmin_test_member, stripe_test_customer)

    def test_eq_customer(self) -> None:
        makeradmin_test_member_A = self.db.create_member(
            firstname="customer",
            lastname="test",
            email="testA@makerspace.se",
        )
        makeradmin_test_member_B = self.db.create_member(
            firstname="customer",
            lastname="test",
            email="testB@makerspace.se",
        )
        self.seen_members.append(makeradmin_test_member_A)
        self.seen_members.append(makeradmin_test_member_B)
        stripe_test_customer_A = get_or_create_stripe_customer(makeradmin_test_member_A)
        stripe_test_customer_B = get_or_create_stripe_customer(makeradmin_test_member_B)
        assert eq_makeradmin_stripe_customer(makeradmin_test_member_A, stripe_test_customer_A)
        assert eq_makeradmin_stripe_customer(makeradmin_test_member_B, stripe_test_customer_B)
        assert not eq_makeradmin_stripe_customer(makeradmin_test_member_A, stripe_test_customer_B)
        assert not eq_makeradmin_stripe_customer(makeradmin_test_member_B, stripe_test_customer_A)

        stripe_test_customer_A.email = "new_email@makerspace.se"
        assert not eq_makeradmin_stripe_customer(makeradmin_test_member_A, stripe_test_customer_A)

    def test_get_sync_customer(self) -> None:
        makeradmin_test_member = self.db.create_member(
            firstname="customer",
            lastname="test",
            email="test@makerspace.se",
        )
        self.seen_members.append(makeradmin_test_member)
        get_and_sync_stripe_customer(makeradmin_test_member)
        makeradmin_test_member.email = "new_email@makerspace.se"
        stripe_test_customer = get_and_sync_stripe_customer(makeradmin_test_member)
        self.assert_customer(makeradmin_test_member, stripe_test_customer)
