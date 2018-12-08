from random import randint

import stripe

from library.base import ApiTest, get_env
from library.factory import PASSWORD


def card(number):
    return {
        "number": str(number),
        "exp_month": 12,
        "exp_year": 2030,
        "cvc": '123'
    }


VALID_NON_3DS_CARD = card("378282246310005")


# TODO Make this better.
stripe.api_key = get_env("STRIPE_PUBLIC_KEY")


class Test(ApiTest):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
    
    def setUp(self):
        super().setUp()
        if not stripe.api_key:
            self.skipTest("No Stripe API key set in the .env file")
            
        # TODO Move to setup class when possible.
        self.category = self.api_create_category()
        cat_id = self.category['id']
        
        self.p1_price = 12.3
        self.p1 = self.api_create_product(price=self.p1_price, unit="st", smallest_multiple=1, category_id=cat_id)
        self.p1_id = self.p1['id']
        
        self.p2_price = 1.2
        self.p2 = self.api_create_product(price=self.p2_price, unit="mm", smallest_multiple=100, category_id=cat_id)
        self.p2_id = self.p2['id']
        self.p2_price = float(self.p2['price'])

        self.member = self.api_create_member()
        self.member_id = self.member['member_id']
        
        pwd = '1q2w3e'

        self.token = self\
            .post("/oauth/token", {"grant_type": "password", "username": self.member["email"], "password": PASSWORD})\
            .expect(code=200)\
            .get("access_token")
        
    def test_valid_purchase_from_existing_member(self):
        
        p1_count = 100
        p2_count = 500
        
        expected_sum = self.p1_price * p1_count + self.p2_price * p2_count
        cart = [
            {"id": self.p1_id, "count": p1_count},
            {"id": self.p2_id, "count": p2_count},
        ]
        
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=VALID_NON_3DS_CARD).id)
        
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
            [{"amount": f"{self.p1_price * p1_count:.2f}", "product_id": self.p1_id},
             {"amount": f"{self.p2_price * p2_count:.2f}", "product_id": self.p2_id}],
            [dict(amount=item['amount'], product_id=item['product_id']) for item in data]
        )

    def test_registring_new_member(self):
        return
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=card(VALID_NON_3DS_CARD_NO)).id)

        member = MemberFactory()

        register = {
            "purchase": {
                "cart": [
                    {
                        "id": self.p1_id,
                        "count": 1,
                    }
                ],
                "expectedSum": "12.30",
                "duplicatePurchaseRand": randint(1e9, 9e9),
                "stripeSource": source.id,
                "stripeThreeDSecure": source["card"]["three_d_secure"]
            },
            "member": member
        }

        transaction_id = self.post(f"/webshop/register", register, token=token).expect(code=200, status="ok").get('data__transaction_id')

        transaction_id = self.post(f"/webshop/register", register, 200, token=token, expected_result={"status": "ok"})["data"]["transaction_id"]
        registered_member_id = self.get(f"/webshop/transaction/{transaction_id}", 200, token=token, expected_result={
            "status": "ok",
            "data": {
                "amount": "12.30",
                "status": "completed"
            },
        })["data"]["member_id"]

        before_activation = self.get(f"/membership/member/{registered_member_id}", 200, expected_result={"data": register["member"]})["data"]
        self.assertIsNotNone(before_activation['deleted_at'])
        self.put(f"/webshop/process_stripe_events", {'start': stripe_start_timestamp}, 200)
        after_activation = self.get(f"/membership/member/{registered_member_id}", 200, expected_result={"data": register["member"]})["data"]
        self.assertIsNone(after_activation['deleted_at'])
        
        
        
        # TODO
        # Test registering a new member

        actions = self.get("/webshop/action")["data"]
        add_membership_days = [a for a in actions if a["name"] == 'add_membership_days'][0]

        action = {
            "product_id": created_product1["id"],
            "action_id": add_membership_days["id"],
            "value": 10
        }
        # Add action to product 1
        self.post(f"/webshop/product_action", action, 200, expected_result={"status": "created", "data": action})["data"]

        source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_TEST_CARD).id)
        duplicatePurchaseRand += 1
        register = {
            "purchase": {
                "cart": [
                    {
                        "id": created_product1["id"],
                        "count": 1,
                    }
                ],
                "expectedSum": "12.30",
                "duplicatePurchaseRand": duplicatePurchaseRand,
                "stripeSource": source.id,
                "stripeThreeDSecure": source["card"]["three_d_secure"]
            },
            "member": {
                "email": f"register{i}@test3",
                "firstname": "test",
                "lastname": "testsson",
                "civicregno": "012345679",
                "company": "ACME",
                "orgno": "01235",
                "address_street": "Teststreet",
                "address_extra": "N/A",
                "address_zipcode": 1235,  # Note: not a string apparently
                "address_city": "Testy Town",
                "address_country": "TS",  # Note: max length 2
                "phone": "01234567",
            }
        }
        transaction_id = self.post(f"/webshop/register", register, 200, token=token, expected_result={"status": "ok"})["data"]["transaction_id"]
        registered_member_id = self.get(f"/webshop/transaction/{transaction_id}", 200, token=token, expected_result={
            "status": "ok",
            "data": {
                "amount": "12.30",
                "status": "completed"
            },
        })["data"]["member_id"]

        before_activation = self.get(f"/membership/member/{registered_member_id}", 200, expected_result={"data": register["member"]})["data"]
        self.assertIsNotNone(before_activation['deleted_at'])
        self.put(f"/webshop/process_stripe_events", {'start': stripe_start_timestamp}, 200)
        after_activation = self.get(f"/membership/member/{registered_member_id}", 200, expected_result={"data": register["member"]})["data"]
        self.assertIsNone(after_activation['deleted_at'])




    def test_count_not_of_correct_multiple_fails_purchase(self):
        purchase = {
            "cart": [{"id": self.p2_id, "count": 17}],
            "expectedSum": f"{self.p2_price * 17:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="InvalidItemCountMultiple")
    
    def test_invalid_expected_sum_fails_purchase(self):
        purchase = {
            "cart": [{"id": self.p1_id, "count": 1}],
            "expectedSum": f"{self.p1_price + 1:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="NonMatchingSums")
    
    def test_negative_count_fails_purchaste(self):
        purchase = {
            "cart": [{"id": self.p1_id, "count": -1}],
            "expectedSum": f"{self.p1_price:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="NonNegativeItemCount")
    
    def test_empty_cart_fails_purchase(self):
        purchase = {
            "cart": [],
            "expectedSum": f"{self.p1_price:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": "not_used",
            "stripeThreeDSecure": "not_used",
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="EmptyCart")
        
    def test_repeated_purchase_rand_fails_purchase(self):
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=VALID_NON_3DS_CARD).id)

        duplicate_purchase_rand = randint(1e9, 9e9)

        purchase = {
            "cart": [{"id": self.p1_id, "count": 1}],
            "expectedSum": f"{self.p1_price:.2f}",
            "duplicatePurchaseRand": duplicate_purchase_rand,
            "stripeSource": source.id,
            "stripeThreeDSecure": source["card"]["three_d_secure"]
        }

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=200, status="ok")

        self.post(f"/webshop/pay", purchase, token=self.token).expect(code=400, status="DuplicateTransaction")
