from random import randint

import stripe

from library.base import ApiTest, get_env
from library.factory import MemberFactory


def card(number):
    return {
        "number": str(number),
        "exp_month": 12,
        "exp_year": 2030,
        "cvc": '123'
    }


VALID_NON_3DS_CARD_NO = "378282246310005"


# TODO Make this better.
stripe.api_key = get_env("STRIPE_PUBLIC_KEY")


class Test(ApiTest):
    
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

    def test_valid_purchase_from_existing_member(self):
        member = self.api_create_member()
        email = member["email"]
        pwd = '1q2w3e'
        
        p1_count = 100
        p2_count = 500
        
        token = self\
            .post("/oauth/token", {"grant_type": "password", "username": email, "password": pwd})\
            .expect(code=200)\
            .get("access_token")
        
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=card(VALID_NON_3DS_CARD_NO)).id)
        expected_sum = self.p1_price * p1_count + self.p2_price * p2_count
        cart = [
            {"id": self.p1_id, "count": p1_count},
            {"id": self.p2_id, "count": p2_count},
        ]
        
        purchase = {
            "cart": cart,
            "expectedSum": f"{expected_sum:.2f}",
            "duplicatePurchaseRand": randint(1e9, 9e9),
            "stripeSource": source.id,
            "stripeThreeDSecure": source["card"]["three_d_secure"]
        }

        transaction_id = self.post(f"/webshop/pay", purchase, token=token).expect(code=200, status="ok").get('data__transaction_id')
        
        self.get(f"/webshop/transaction/{transaction_id}").print().expect(
            code=200,
            status="ok",
            data__amount=f"{expected_sum:.2f}",
            data__member_id=member['member_id'],
            data__status="completed",
        )

        data = self.get(f"/webshop/transaction/{transaction_id}/content").expect(code=200, status="ok").data
        self.assertCountEqual(
            [{"amount": f"{self.p1_price * p1_count:.2f}", "product_id": self.p1_id},
             {"amount": f"{self.p2_price * p2_count:.2f}", "product_id": self.p2_id}],
            [dict(amount=item['amount'], product_id=item['product_id']) for item in data]
        )

    # TODO
    # def test_registring_new_member(self):
    #     source = stripe.Source.create(type="card", token=stripe.Token.create(card=card(VALID_NON_3DS_CARD_NO)).id)
    #
    #     member = MemberFactory()
    #
    #     register = {
    #         "purchase": {
    #             "cart": [
    #                 {
    #                     "id": self.p1_id,
    #                     "count": 1,
    #                 }
    #             ],
    #             "expectedSum": "12.30",
    #             "duplicatePurchaseRand": randint(1e9, 9e9),
    #             "stripeSource": source.id,
    #             "stripeThreeDSecure": source["card"]["three_d_secure"]
    #         },
    #         "member": member
    #     }
    #
    #     transaction_id = self.post(f"/webshop/register", register, token=token).expect(code=200, status="ok").get('data__transaction_id')
    #
    #     transaction_id = self.post(f"/webshop/register", register, 200, token=token, expected_result={"status": "ok"})["data"]["transaction_id"]
    #     registered_member_id = self.get(f"/webshop/transaction/{transaction_id}", 200, token=token, expected_result={
    #         "status": "ok",
    #         "data": {
    #             "amount": "12.30",
    #             "status": "completed"
    #         },
    #     })["data"]["member_id"]
    #
    #     before_activation = self.get(f"/membership/member/{registered_member_id}", 200, expected_result={"data": register["member"]})["data"]
    #     self.assertIsNotNone(before_activation['deleted_at'])
    #     self.put(f"/webshop/process_stripe_events", {'start': stripe_start_timestamp}, 200)
    #     after_activation = self.get(f"/membership/member/{registered_member_id}", 200, expected_result={"data": register["member"]})["data"]
    #     self.assertIsNone(after_activation['deleted_at'])


class TestFailedPurchase(ApiTest):
    
    def setUp(self):
        super().setUp()
        if not stripe.api_key:
            self.skipTest("No Stripe API key set in the .env file")

    def count_not_of_correct_multiple_fails_purchase(self):
        pass
    
    def invalid_expected_sum_fails_purchase(self):
        pass
    
    def negative_counts_fails_purchaste(self):
        pass
    
    def empty_cart_fails_purchase(self):
        pass
        
    def declined_card_fails_purchase(self):
        pass
        
    def repeated_purchase_rand_fails_purchase(self):
        pass
 
        source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_TEST_CARD).id)

                # Product 2 can only be purchased in multiples of 100
                make_failed_purchase(source, member_id, token, zip([created_product2], [7]), 400, expected_result={"status": "InvalidItemCountMultiple"})

                # Invalid expected sum
                duplicatePurchaseRand += 1
                purchase = {
                    "cart": [
                        {
                            "id": created_product1["id"],
                            "count": 3,
                        },
                        {
                            "id": created_product2["id"],
                            "count": 100,
                        }
                    ],
                    "expectedSum": "19.20",
                    "duplicatePurchaseRand": duplicatePurchaseRand,
                    "stripeSource": source.id,
                    "stripeThreeDSecure": source["card"]["three_d_secure"]
                }
                self.post(f"/webshop/pay", purchase, 400, token=token, expected_result={"status": "NonMatchingSums"})

                # Negative amounts
                make_failed_purchase(source, member_id, token, zip([created_product2], [-3]), 400, expected_result={"status": "NonNegativeItemCount"})

                # Empty cart
                make_failed_purchase(source, member_id, token, zip([], []), 400, expected_result={"status": "EmptyCart"})

                # Card that will be declined
                STRIPE_DECLINE_CARD = {
                    "number": "4000000000000002",
                    "exp_month": 12,
                    "exp_year": 2019,
                    "cvc": '123'
                }
                source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_DECLINE_CARD).id)
                make_failed_purchase(source, member_id, token, zip([created_product2], [-3]), 400, expected_result={"status": "NonNegativeItemCount"})
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

    


    def test_purchase(self):
        if not stripe.api_key:
            self.skipTest("No Stripe API key set in the .env file")

        stripe_start_timestamp = self.put(f"/webshop/process_stripe_events", {}, 200)['data']['start']

        def prepare_purchase(source, productsAndCounts):
            global duplicatePurchaseRand
            duplicatePurchaseRand += 1
            expected_sum = str(sum(Decimal(p["price"]) * c for (p,c) in productsAndCounts))
            purchase = {
                "cart": [{"id": p["id"], "count": c} for (p, c) in productsAndCounts],
                "expectedSum": str(sum(Decimal(p["price"]) * c for (p, c) in productsAndCounts)),  # "156.9",
                "duplicatePurchaseRand": duplicatePurchaseRand,
                "stripeSource": source.id,
                "stripeThreeDSecure": source["card"]["three_d_secure"]
            }
            return purchase, expected_sum

        def make_valid_purchase(source, member_id, member_login_token, productsAndCounts):
            # Make sure it is a list and not some other consumable iterator
            productsAndCounts = list(productsAndCounts)

            purchase, expected_sum = prepare_purchase(source, productsAndCounts)

            # Make a valid purchase
            transaction_id = self.post(f"/webshop/pay", purchase, 200, token=member_login_token, expected_result={"status": "ok"})["data"]["transaction_id"]

            # Verify the transaction
            self.get(f"/webshop/transaction/{transaction_id}", 200, token=member_login_token, expected_result={
                "status": "ok",
                "data": {
                    "amount": expected_sum,
                    "member_id": member_id,
                    "status": "completed"
                },
            })

            # Verify the contents
            self.get(f"/webshop/transaction/{transaction_id}/content", 200, token=member_login_token, expected_result={
                "status": "ok",
                "data": [
                    {
                        "amount": str(Decimal(p["price"]) * c),
                        "count": c,
                        "product_id": p["id"],
                        "product_name": p["name"],
                    }
                    for (p,c) in productsAndCounts
                ]
            })

        def make_failed_purchase(source, member_id, member_login_token, productsAndCounts, status_code, expected_result):
            # Make sure it is a list and not some other consumable iterator
            productsAndCounts = list(productsAndCounts)

            purchase, expected_sum = prepare_purchase(source, productsAndCounts)

            # Make an invalid purchase
            self.post(f"/webshop/pay", purchase, status_code, token=member_login_token, expected_result=expected_result)

        def create_test_products():
            category = {
                "name": "Blah"
            }
            created_category = self.post(f"/webshop/category", category, 200, expected_result={"status": "created", "data": category})["data"]

            product1 = {
                "name": "Meh",
                "price": "12.30",
                "description": "This is a description",
                "unit": "st",
                "smallest_multiple": 1,
                "filter": None,
                "category_id": created_category["id"],
            }
            created_product1 = self.post(f"/webshop/product", product1, 200, expected_result={"status": "created", "data": product1})["data"]

            product2 = {
                "name": "Meh2",
                "price": "1.20",
                "description": "This is not a description",
                "unit": "mm",
                "smallest_multiple": 100,
                "filter": None,
                "category_id": created_category["id"],
            }
            created_product2 = self.post(f"/webshop/product", product2, 200, expected_result={"status": "created", "data": product2})["data"]
            return created_product1, created_product2

        global duplicatePurchaseRand

        with MemberDummies(self, 1) as created_members:
            for i, (member, password) in enumerate(created_members):
                member_id = member['member_id']

                created_product1, created_product2 = create_test_products()

                token = self.post(f"/oauth/token", {"grant_type": "password", "username": member["email"], "password": password}, 200)["access_token"]
                STRIPE_TEST_CARD = {
                    "number": '378 282 246 310 005',
                    "exp_month": 12,
                    "exp_year": 2019,
                    "cvc": '123'
                }

                # This is currently disabled because these cards have 3D secure set as optional
                # and the backend will try to use that then. However it is tricky to unit test 3D secure.
                if False:
                    # Test various cards
                    # Note: some are commented out because it takes a ridiculously long time to run the tests.
                    # One card of each type seems sufficient.
                    valid_cards = [
                        "4242424242424242",  # Visa
                        "4000056655665556",  # Visa (debit)
                        "5555555555554444",  # Mastercard
                        # "2223003122003222",  # Mastercard (2-series)
                        # "5200828282828210",  # Mastercard (debit)
                        # "5105105105105100",  # Mastercard (prepaid)
                        "378282246310005",   # American Express
                        # "371449635398431",   # American Express
                    ]

                    for card in valid_cards:
                        card_info = {
                            "number": card,
                            "exp_month": 12,
                            "exp_year": 2030,
                            "cvc": '123'
                        }
                        source = stripe.Source.create(type="card", token=stripe.Token.create(card=card_info).id)
                        make_valid_purchase(source, member_id, token, zip([created_product1, created_product2], [3, 100]))
                else:
                    # Make a valid purchase using a card that does not support 3D secure
                    source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_TEST_CARD).id)
                    make_valid_purchase(source, member_id, token, zip([created_product1, created_product2], [3, 100]))

                # Make some invalid purchases

                source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_TEST_CARD).id)

                # Product 2 can only be purchased in multiples of 100
                make_failed_purchase(source, member_id, token, zip([created_product2], [7]), 400, expected_result={"status": "InvalidItemCountMultiple"})

                # Invalid expected sum
                duplicatePurchaseRand += 1
                purchase = {
                    "cart": [
                        {
                            "id": created_product1["id"],
                            "count": 3,
                        },
                        {
                            "id": created_product2["id"],
                            "count": 100,
                        }
                    ],
                    "expectedSum": "19.20",
                    "duplicatePurchaseRand": duplicatePurchaseRand,
                    "stripeSource": source.id,
                    "stripeThreeDSecure": source["card"]["three_d_secure"]
                }
                self.post(f"/webshop/pay", purchase, 400, token=token, expected_result={"status": "NonMatchingSums"})

                # Negative amounts
                make_failed_purchase(source, member_id, token, zip([created_product2], [-3]), 400, expected_result={"status": "NonNegativeItemCount"})

                # Empty cart
                make_failed_purchase(source, member_id, token, zip([], []), 400, expected_result={"status": "EmptyCart"})

                # Card that will be declined
                STRIPE_DECLINE_CARD = {
                    "number": "4000000000000002",
                    "exp_month": 12,
                    "exp_year": 2019,
                    "cvc": '123'
                }
                source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_DECLINE_CARD).id)
                make_failed_purchase(source, member_id, token, zip([created_product2], [-3]), 400, expected_result={"status": "NonNegativeItemCount"})
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

    
