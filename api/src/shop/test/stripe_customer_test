from logging import getLogger
from typing import Any, Dict, List
from unittest import skipIf

import membership.models
import shop.models
import messages.models
import core.models
from shop.stripe_customer import (
    get_or_create_stripe_customer,
    get_and_sync_stripe_customer,
    delete_stripe_customer,
    eq_makeradmin_stripe_customer,
)
from shop.stripe_util import are_metadata_dicts_equivalent
from shop.stripe_constants import (
    MakerspaceMetadataKeys as MSMetaKeys,
)
from membership.models import Member
import stripe
from test_aid.test_base import FlaskTestBase, ShopTestMixin

logger = getLogger("makeradmin")


class StripeCustomerTest(ShopTestMixin, FlaskTestBase):
    # The products id in makeradmin have to be unique in each test to prevent race conditions
    # Some of the tests here will generate new objects in stripe. They are all ran in test mode
    # You can clear the test area in stripe's developer dashboard.

    models = [membership.models, messages.models, shop.models, core.models]

    @skipIf(not stripe.api_key, "stripe util tests require stripe api key in .env file")
    def setUp(self) -> None:
        self.seen_members: List[Member] = []

    def tearDown(self) -> None:
        # It is not possible to delete prices through the api so we set them as inactive instead
        for makeradmin_member in self.seen_members:
            delete_stripe_customer(makeradmin_member.member_id)
            return super().tearDown()

    @staticmethod
    def assertCustomer(makeradmin_member: Member, stripe_test_customer: stripe.Customer) -> None:
        assert stripe_test_customer
        assert stripe_test_customer.email == makeradmin_member.email.strip()
        expected_metadata = {
            # Setting to an empty string will delete the key if present
            MSMetaKeys.PENDING_MEMBER.value: "pending" if makeradmin_member.pending_activation else "",
            MSMetaKeys.USER_ID.value: makeradmin_member.member_id,
            MSMetaKeys.MEMBER_NUMBER.value: makeradmin_member.member_number,
        }
        assert are_metadata_dicts_equivalent(stripe_test_customer.metadata, expected_metadata)

    def test_create_customer(self) -> None:
        makeradmin_test_member = self.db.create_member(
            first_name="test customer simple",
            email="simple_test@makerspace.se",
        )
        self.seen_members.append(makeradmin_test_member)
        stripe_test_customer = get_or_create_stripe_customer(makeradmin_test_member)
        self.assertCustomer(makeradmin_test_member, stripe_test_customer)

    # TODO more tests
