from logging import getLogger


import stripe
from shop.transactions import CartItem, Purchase

from test_aid.systest_base import ApiShopTestMixin, ApiTest, VALID_NON_3DS_CARD_NO, VALID_3DS_CARD_NO, retry

logger = getLogger("makeradmin")


class Test(ApiShopTestMixin, ApiTest):
    products = [
        dict(price=12.3, unit="st", smallest_multiple=1),
        dict(price=1.2, unit="mm", smallest_multiple=100),
    ]

    def test_purchase_from_existing_member_using_non_3ds_card_works(self) -> None:
        p0_count = 100
        p1_count = 500

        expected_sum = self.p0_price * p0_count + self.p1_price * p1_count
        cart = [
            CartItem(self.p0_id, p0_count),
            CartItem(self.p1_id, p1_count),
        ]

        payment_method = stripe.PaymentMethod.create(type="card", card=self.card(VALID_NON_3DS_CARD_NO))

        purchase = Purchase(
            cart=cart,
            expected_sum=expected_sum,
            stripe_payment_method_id=payment_method.id,
        )

        transaction_id = (
            self.post(f"/webshop/pay", purchase.to_dict(), token=self.token)
            .expect(code=200, status="ok")
            .get("data__transaction_id")
        )

        self.get(f"/webshop/transaction/{transaction_id}").expect(
            code=200,
            status="ok",
            data__amount=f"{expected_sum:.2f}",
            data__member_id=self.member_id,
            data__status="completed",
        )

        data = self.get(f"/webshop/transaction/{transaction_id}/contents").expect(code=200, status="ok").data
        self.assertCountEqual(
            [
                {"amount": f"{self.p0_price * p0_count:.2f}", "product_id": self.p0_id},
                {"amount": f"{self.p1_price * p1_count:.2f}", "product_id": self.p1_id},
            ],
            [dict(amount=item["amount"], product_id=item["product_id"]) for item in data],
        )

    def test_purchase_from_existing_member_using_auto_validating_3ds_card_works(self) -> None:
        p0_count = 100
        p1_count = 500

        expected_sum = self.p0_price * p0_count + self.p1_price * p1_count
        cart = [
            CartItem(self.p0_id, p0_count),
            CartItem(self.p1_id, p1_count),
        ]

        payment_method = stripe.PaymentMethod.create(type="card", card=self.card(VALID_3DS_CARD_NO))

        purchase = Purchase(
            cart=cart,
            expected_sum=expected_sum,
            stripe_payment_method_id=payment_method.id,
        )

        transaction_id = (
            self.post(f"/webshop/pay", purchase.to_dict(), token=self.token)
            .expect(code=200, status="ok")
            .get("data__transaction_id")
        )

        def assert_transation() -> None:
            self.get(f"/webshop/transaction/{transaction_id}").expect(
                code=200,
                status="ok",
                data__amount=f"{expected_sum:.2f}",
                data__member_id=self.member_id,
                data__status="completed",
            )

        retry(retry_exception=lambda e: isinstance(e, AssertionError))(assert_transation)()

        data = self.get(f"/webshop/transaction/{transaction_id}/contents").expect(code=200, status="ok").data
        self.assertCountEqual(
            [
                {"amount": f"{self.p0_price * p0_count:.2f}", "product_id": self.p0_id},
                {"amount": f"{self.p1_price * p1_count:.2f}", "product_id": self.p1_id},
            ],
            [dict(amount=item["amount"], product_id=item["product_id"]) for item in data],
        )

    def test_count_not_of_correct_multiple_fails_purchase(self) -> None:
        purchase = Purchase(
            cart=[CartItem(self.p1_id, 17)],
            expected_sum=self.p1_price * 17,
            stripe_payment_method_id="not_used",
        )

        self.post(f"/webshop/pay", purchase.to_dict(), token=self.token).expect(code=400, what="invalid_item_count")

    def test_invalid_expected_sum_fails_purchase(self) -> None:
        purchase = Purchase(
            cart=[CartItem(self.p0_id, 1)],
            expected_sum=self.p0_price + 1,
            stripe_payment_method_id="not_used",
        )

        self.post(f"/webshop/pay", purchase.to_dict(), token=self.token).expect(code=400, what="non_matching_sums")

    def test_negative_count_fails_purchaste(self) -> None:
        purchase = Purchase(
            cart=[CartItem(self.p0_id, -1)],
            expected_sum=self.p0_price,
            stripe_payment_method_id="not_used",
        )

        self.post(f"/webshop/pay", purchase.to_dict(), token=self.token).expect(code=400, what="negative_item_count")

    def test_empty_cart_fails_purchase(self) -> None:
        purchase = Purchase(
            cart=[],
            expected_sum=self.p0_price,
            stripe_payment_method_id="not_used",
        )

        self.post(f"/webshop/pay", purchase.to_dict(), token=self.token).expect(code=400, what="empty_cart")
