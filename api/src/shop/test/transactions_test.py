from decimal import Decimal

import membership.models
import shop.models
from service.db import db_session
from shop.transactions import get_source_transaction
from test_aid.test_base import FlaskTestBase


class ShopDataTest(FlaskTestBase):
    models = [membership.models, shop.models]

    def test_finds_transaction_for_stripe_pending(self) -> None:
        member = self.db.create_member()
        transaction = self.db.create_transaction(
            member_id=member.member_id,
            amount=Decimal("50"),
            status=shop.models.Transaction.PENDING,
        )
        pending = shop.models.StripePending(
            transaction_id=transaction.id,
            stripe_token="stripe_token",
        )
        db_session.add(pending)
        db_session.commit()

        found_transaction = get_source_transaction("stripe_token")
        self.assertIsNotNone(found_transaction)
        self.assertEqual(transaction.id, found_transaction.id)
