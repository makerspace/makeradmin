from random import randint
from unittest import skip

import stripe

from library.api import ApiTest
from library.base import ShopTestMixin, VALID_NON_3DS_CARD_NO


class Test(ShopTestMixin, ApiTest):

    products = [
        dict(price=12.3, unit="st", smallest_multiple=1),
        dict(price=1.2, unit="mm", smallest_multiple=100),
    ]

    def test_valid_purchase_from_existing_member(self):
        p0_count = 100
        p1_count = 500
        
        expected_sum = self.p0_price * p0_count + self.p1_price * p1_count
        cart = [
            {"id": self.p0_id, "count": p0_count},
            {"id": self.p1_id, "count": p1_count},
        ]
        
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=self.VALID_NON_3DS_CARD).id)
        
        purchase = {
            "cart": cart,
            "expectedSum": f"{expected_sum:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": source.id,
            "stripeThreeDSecure": source["card"]["three_d_secure"]
        }

        transaction_id = self.post(f"/webshop/pay", purchase, token=self.token)\
            .expect(code=200, status="ok").get('data__transaction_id')
        
        self.get(f"/webshop/transaction/{transaction_id}").expect(
            code=200,
            status="ok",
            data__amount=f"{expected_sum:.2f}",
            data__member_id=self.member_id,
            data__status="completed",
        )

        data = self.get(f"/webshop/transaction/{transaction_id}/content").expect(code=200, status="ok").data
        self.assertCountEqual(
            [{"amount": f"{self.p0_price * p0_count:.2f}", "product_id": self.p0_id},
             {"amount": f"{self.p1_price * p1_count:.2f}", "product_id": self.p1_id}],
            [dict(amount=item['amount'], product_id=item['product_id']) for item in data]
        )

    def test_count_not_of_correct_multiple_fails_purchase(self):
        purchase = {
            "cart": [{"id": self.p1_id, "count": 17}],
            "expectedSum": f"{self.p1_price * 17:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="InvalidItemCountMultiple")
    
    def test_invalid_expected_sum_fails_purchase(self):
        purchase = {
            "cart": [{"id": self.p0_id, "count": 1}],
            "expectedSum": f"{self.p0_price + 1:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="NonMatchingSums")
    
    def test_negative_count_fails_purchaste(self):
        purchase = {
            "cart": [{"id": self.p0_id, "count": -1}],
            "expectedSum": f"{self.p0_price:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="NonNegativeItemCount")
    
    def test_empty_cart_fails_purchase(self):
        purchase = {
            "cart": [],
            "expectedSum": f"{self.p0_price:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="EmptyCart")
        
    @skip("duplicate purchase rand does not work reliably and can not be tested, see issue #35")
    def test_repeated_purchase_rand_fails_purchase(self):
        duplicate_purchase_rand = randint(1e9, 9e9)

        source = stripe.Source.create(type="card", token=stripe.Token.create(card=self.card(VALID_NON_3DS_CARD_NO)).id)
        purchase = {
            "cart": [{"id": self.p0_id, "count": 1}],
            "expectedSum": f"{self.p0_price:.2f}",
            "duplicatePurchaseRand": duplicate_purchase_rand,
            "stripeSource": source.id,
            "stripeThreeDSecure": source["card"]["three_d_secure"]
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=200, status="ok")
        
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=self.card(VALID_NON_3DS_CARD_NO)).id)
        purchase['stripeSource'] = source.id

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="DuplicateTransaction")
