from random import randint
from time import time

import stripe
from membership.models import Span
from service.api_definition import NON_MATCHING_SUMS
from service.db import db_session
from shop.models import ProductAction
from shop.pay import MemberInfo, RegisterRequest
from shop.stripe_constants import MakerspaceMetadataKeys
from shop.stripe_payment_intent import PaymentIntentResult
from shop.stripe_subscriptions import SubscriptionType
from shop.stripe_util import retry
from shop.transactions import CartItem, Purchase
from test_aid.systest_base import EXPIRED_3DS_CARD_NO, VALID_NON_3DS_CARD_NO, ApiShopTestMixin, ApiTest


class Test(ApiShopTestMixin, ApiTest):
    products = [
        dict(
            smallest_multiple=1,
            price=300.0,
            action=dict(action_type=ProductAction.ADD_MEMBERSHIP_DAYS, value=365),
            product_metadata={
                MakerspaceMetadataKeys.SPECIAL_PRODUCT_ID.value: "special_test_product_please_ignore",
                MakerspaceMetadataKeys.SUBSCRIPTION_TYPE.value: SubscriptionType.MEMBERSHIP.value,
            },
        )
    ]

    def test_registering_new_member_works_and_returns_token(self) -> None:
        payment_method = retry(lambda: stripe.PaymentMethod.create(type="card", card=self.card(VALID_NON_3DS_CARD_NO)))

        member = self.obj.create_member()
        register: RegisterRequest = RegisterRequest(
            member=MemberInfo(
                firstName=member["firstname"],
                lastName=member["lastname"],
                email=member["email"],
                phone=member["phone"],
                zipCode=member["address_zipcode"],
            ),
            discount=None,
        )

        member_id, token = (
            self.post(f"/webshop/register", register.to_dict(), headers={})
            .expect(code=200, status="ok")
            .get("data__member_id", "data__token")
        )

        self.assertIsNotNone(token)

        before_activation = (
            self.get(f"/membership/member/{member_id}")
            .expect(
                code=200,
                data={
                    "firstname": member["firstname"],
                    "lastname": member["lastname"],
                    "email": member["email"],
                    "address_zipcode": member["address_zipcode"],
                },
            )
            .data
        )

        self.assertIsNotNone(before_activation["deleted_at"])

        purchase = Purchase(
            cart=[CartItem(self.p0_id, 1)],
            expected_sum="300",
            stripe_payment_method_id=payment_method.id,
        )
        self.post(f"/webshop/pay", purchase.to_dict(), token=token).expect(
            code=200, status="ok", data={"type": PaymentIntentResult.Success.value}
        )

        after_activation = self.get(f"/membership/member/{member_id}").expect(code=200).data
        self.assertIsNone(after_activation["deleted_at"])

        span = db_session.query(Span).filter_by(member_id=member_id, type=Span.MEMBERSHIP).one()
        self.assertEqual(self.date(365), span.enddate)

    def test_registering_new_member_fails_with_invalid_email(self) -> None:
        member = self.obj.create_member()
        member["email"] = member["email"].replace("@", "_")

        register: RegisterRequest = RegisterRequest(
            member=MemberInfo(
                firstName=member["firstname"],
                lastName=member["lastname"],
                email=member["email"],
                phone=member["phone"],
                zipCode=member["address_zipcode"],
            ),
            discount=None,
        )

        self.post(f"/webshop/register", register.to_dict(), headers={}).expect(
            data__token=None, code=422, message="Email is not valid."
        )

    def test_registering_with_existing_member_email_does_not_work_and_does_not_return_token(self) -> None:
        member = self.obj.create_member()
        self.api.create_member(**member)

        register: RegisterRequest = RegisterRequest(
            member=MemberInfo(
                firstName=member["firstname"],
                lastName=member["lastname"],
                email=member["email"],
                phone=member["phone"],
                zipCode=member["address_zipcode"],
            ),
            discount=None,
        )

        self.post(f"/webshop/register", register.to_dict(), headers={}).expect(
            data__token=None, code=422, what="not_unique", fields="email"
        )

    def test_registering_with_failed_payment_does_not_work_and_does_not_return_token(self) -> None:
        payment_method = retry(lambda: stripe.PaymentMethod.create(type="card", card=self.card(EXPIRED_3DS_CARD_NO)))

        member = self.obj.create_member()

        register: RegisterRequest = RegisterRequest(
            member=MemberInfo(
                firstName=member["firstname"],
                lastName=member["lastname"],
                email=member["email"],
                phone=member["phone"],
                zipCode=member["address_zipcode"],
            ),
            discount=None,
        )

        (member_id, token) = (
            self.post(f"/webshop/register", register.to_dict(), headers={})
            .expect(code=200)
            .get("data__member_id", "data__token")
        )

        purchase = Purchase(
            cart=[CartItem(self.p0_id, 1)],
            expected_sum="121212121.00",
            stripe_payment_method_id=payment_method.id,
        )

        self.post(f"/webshop/pay", purchase.to_dict(), token=token).expect(code=400, what="non_matching_sums")
