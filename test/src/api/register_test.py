import sys
from random import randint
from time import time

import stripe

from library.api import ApiTest
from library.base import ShopTestMixin, VALID_NON_3DS_CARD_NO, EXPIRED_3DS_CARD_NO
from library.obj import ADD_MEMBERSHIP_DAYS


class Test(ShopTestMixin, ApiTest):

    products = [
        dict(
            smallest_multiple=1,
            price=300.0,
            action=dict(action_id=ADD_MEMBERSHIP_DAYS, value=365),
        )
    ]

    def test_registring_new_member_works_and_returns_token(self):
        print(f"TODO test_registring_new_member_works_and_returns_token", file=sys.stderr)
        start_timestamp = int(time())

        source = stripe.Source.create(type="card", token=stripe.Token.create(card=self.card(VALID_NON_3DS_CARD_NO)).id)

        member = self.obj.create_member()

        register = {
            "purchase": {
                "cart": [
                    {
                        "id": self.p0_id,
                        "count": 1,
                    }
                ],
                "expectedSum": "300.00",
                "duplicatePurchaseRand": randint(1e9, 9e9),
                "stripeSource": source.id,
                "stripeThreeDSecure": source["card"]["three_d_secure"]
            },
            "member": member
        }

        transaction_id, token = self\
            .post(f"/webshop/register", register, headers={})\
            .expect(code=200, status="ok")\
            .get('data__transaction_id', 'data__token')

        self.assertIsNotNone(token)

        member_id = self\
            .get(f"/webshop/transaction/{transaction_id}")\
            .expect(code=200, status="ok", data__amount="300.00", data__status="completed")\
            .get('data__member_id')

        before_activation = self.get(f"/membership/member/{member_id}").expect(code=200, data=member).data
        self.assertIsNone(before_activation['deleted_at'])
        
        self.put("/webshop/process_stripe_events", {"source_id": source.id, "start": start_timestamp}).expect(code=200)
        
        after_activation = self.get(f"/membership/member/{member_id}").expect(code=200, data=member).data
        self.assertIsNone(after_activation['deleted_at'])

    def test_registring_with_existing_member_email_does_not_work_and_does_not_return_token(self):
        print(f"TODO test_registring_with_existing_member_email_does_not_work_and_does_not_return_token", file=sys.stderr)
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=self.card(VALID_NON_3DS_CARD_NO)).id)

        member = self.api.create_member()

        register = {
            "purchase": {
                "cart": [
                    {
                        "id": self.p0_id,
                        "count": 1,
                    }
                ],
                "expectedSum": "300.00",
                "duplicatePurchaseRand": randint(1e9, 9e9),
                "stripeSource": source.id,
                "stripeThreeDSecure": source["card"]["three_d_secure"]
            },
            "member": member
        }

        self\
            .post(f"/webshop/register", register, headers={})\
            .expect(data__token=None, code=400, status="RegisterEmailAlreadyExists")\

    def test_registring_with_failed_payment_does_not_work_and_does_not_return_token(self):
        print(f"TODO test_registring_with_failed_payment_does_not_work_and_does_not_return_token", file=sys.stderr)
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=self.card(EXPIRED_3DS_CARD_NO)).id)

        member = self.obj.create_member()

        register = {
            "purchase": {
                "cart": [
                    {
                        "id": self.p0_id,
                        "count": 1,
                    }
                ],
                "expectedSum": "121212121.00",
                "duplicatePurchaseRand": randint(1e9, 9e9),
                "stripeSource": source.id,
                "stripeThreeDSecure": source["card"]["three_d_secure"]
            },
            "member": member
        }

        self\
            .post(f"/webshop/register", register, headers={})\
            .expect(data__token=None, code=400, status="NonMatchingSums")\
