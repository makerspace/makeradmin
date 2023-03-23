from datetime import date, timedelta, datetime, timezone
import logging
import time
import random
import copy
import math
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, cast
from unittest.mock import Mock, patch

import pytest
from shop.stripe_util import event_semantic_time
from test_aid.systest_base import DECLINE_AFTER_ATTACHING_CARD, VALID_3DS_CARD_NO
from shop.stripe_checkout import BINDING_PERIOD, SubscriptionType, get_stripe_customer
from shop import stripe_checkout
from membership.membership import get_membership_summary
from test_aid.test_util import random_str
from membership.member_auth import hash_password
from test_aid.obj import ObjFactory, DEFAULT_PASSWORD
import core
import messages
import shop
import membership
import membership.models
import shop.models
import messages.models
import core.models
from membership.models import Span, Member
from messages.models import Message
import membership.views
from service.db import db_session
from shop.transactions import ship_orders
from test_aid.test_base import FlaskTestBase
import stripe
from shop import stripe_event
from shop import stripe_constants

logger = logging.getLogger("makeradmin")

class FakeClock:
    def __init__(self, date: datetime) -> None:
        self.date = date
        self.stripe_clock = stripe.test_helpers.TestClock.create(
            frozen_time=int(date.timestamp()), name="TestClock"
        )

    def advance(self, to: datetime) -> None:
        assert to >= self.date
        self.date = to
        stripe.test_helpers.TestClock.advance(
            self.stripe_clock.stripe_id, frozen_time=int(self.date.timestamp())
        )


class Test(FlaskTestBase):

    models = [membership.models, messages.models, shop.models, core.models]
    seen_event_ids: Set[str]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Span).delete()
        db_session.query(Message).delete()
        self.seen_event_ids = set()
        self.earliest_possible_event_time = datetime.now(timezone.utc)
        self.clocks_to_destroy: List[FakeClock] = []
        stripe_constants.set_stripe_key(True)

        disable_loggers = ['stripe']

        for logger_name in disable_loggers:
            logger = logging.getLogger(logger_name)
            logger.disabled = True

    def tearDown(self) -> None:
        # Delete all test clocks
        # This will also delete all customers and subscriptions created during the test
        for c in self.clocks_to_destroy:
            stripe.test_helpers.TestClock.delete(c.stripe_clock.stripe_id)
        return super().tearDown()

    def add_span(
        self, member: Member, type: str, startdate: date, enddate: date
    ) -> None:
        span = Span(
            startdate=startdate,
            enddate=enddate,
            type=type,
            member=member,
            creation_reason=random_str(),
        )
        db_session.add(span)
        db_session.commit()

    @staticmethod
    def card(number: str) -> Dict[str, Any]:
        return {"number": number, "exp_month": 12, "exp_year": 2030, "cvc": "123"}

    def create_member_that_can_pay(self, test_clock: FakeClock, signed_labaccess: bool=True) -> Member:
        member = self.db.create_member(password=hash_password(DEFAULT_PASSWORD))
        self.set_payment_method(member, VALID_3DS_CARD_NO, test_clock)
        if signed_labaccess:
            member.labaccess_agreement_at = test_clock.date
        return member

    def set_payment_method(
        self, member: Member, card_number: str, test_clock: FakeClock
    ) -> None:
        payment_method = stripe.PaymentMethod.create(
            type="card", card=self.card(card_number)
        )
        stripe_member = get_stripe_customer(member, test_clock=test_clock.stripe_clock)
        assert stripe_member is not None
        stripe.PaymentMethod.attach(payment_method, customer=stripe_member.stripe_id)
        stripe.Customer.modify(
            stripe_member.stripe_id,
            invoice_settings={
                "default_payment_method": payment_method.stripe_id,
            },
        )

    def get_member(self, member_id: int) -> Member:
        return cast(Member, db_session.query(Member).get(member_id))

    def setup_single_member(self, signed_labaccess: bool=True) -> Tuple[datetime, FakeClock, int]:
        now = datetime.now(timezone.utc)
        clock = FakeClock(now)
        self.clocks_to_destroy.append(clock)
        member_id = self.create_member_that_can_pay(clock, signed_labaccess).member_id
        return (now, clock, member_id)

    def advance_clock(self, clock: FakeClock, time: datetime) -> None:
        clock.advance(to=time)
        logger.info(f"Advancing clock to {time}...")
        # Wait until all stripe events have been received
        # We will query for all events that have been created since this test started.
        # We would like to filter for all events after the test clock's time before we advanced it, but sadly
        # stripe's event listing function only filters based on real-time, not on test clock time.
        self.poll_stripe_events(
            self.earliest_possible_event_time,
            "test_helpers.test_clock.ready",
            clock.stripe_clock.stripe_id,
        )

    def poll_stripe_events(
        self, min_time: datetime, until_seen_type: str, test_clock: str
    ) -> None:
        def test_clock_for_event(event: Any) -> Optional[str]:
            if event["type"].startswith("test_helpers.test_clock."):
                return cast(str, event["data"]["object"]["id"])
            else:
                return cast(
                    Optional[str], event["data"]["object"].get("test_clock", None)
                )

        batched_events: List[stripe.Event] = []
        done = 0

        # Even if we receive for example a test_helpers.test_clock.ready event, we still check
        # a few more times to make sure that we have received all events that were generated.
        # This is because stripe's event list is not guaranteed to contain all events that the clock
        # should generate, EVEN IF IT SAYS THE CLOCK IS READY. So dumb...
        ADDITIONAL_WAIT_SECS = 3
        SLEEP_BETWEEN_POLLS = 1.0
        TIMEOUT_SECS = 20

        its = 0
        while done < 1 + math.ceil(ADDITIONAL_WAIT_SECS / SLEEP_BETWEEN_POLLS):
            its += 1
            if done > 0:
                done += 1

            if its > TIMEOUT_SECS / SLEEP_BETWEEN_POLLS:
                raise Exception(
                    f"Did not receive a {until_seen_type} event in {TIMEOUT_SECS} seconds. Received events: {[ev.type for ev in batched_events]}"
                )

            time.sleep(SLEEP_BETWEEN_POLLS)
            events = stripe.Event.list(created={"gte": int(min_time.timestamp())})
            for ev in events.auto_paging_iter():
                if ev.id in self.seen_event_ids:
                    continue

                # This will filter out all events not associated with the test clock we are interested in.
                # This is useful when we have multiple test clocks running in parallel, which may happen
                # if we have multiple tests running in parallel.
                # Note that this will also filter out all events that are not associated with a test clock.
                # For example charge events will not be associated with a test clock.
                # However, for the subscriptions tests, we don't care about those events.
                if test_clock_for_event(ev) != test_clock:
                    continue

                self.seen_event_ids.add(ev.stripe_id)

                # Do not forward test clock events. They are just debugging noise.
                if not ev.type.startswith("test_helpers.test_clock."):
                    batched_events.append(ev)

                if ev.type == until_seen_type:
                    logger.info(
                        "Clock is ready. Waiting a bit to make sure we have received all events..."
                    )
                    done = 1
                    break

        ORDER = "time"

        if ORDER == "random":
            # Stripe webhook events do not guarantee that they arrive in any particular order.
            # To emulate this, we sort the events based on their time with a random perturbation.
            # This will make sure that the api is not sensitive to the precise order of events.
            MAX_OFFSET_SECONDS = 30
            events_with_random_time = [
                (
                    (
                        int(e["created"])
                        + random.randint(-MAX_OFFSET_SECONDS, MAX_OFFSET_SECONDS)
                    ),
                    e,
                )
                for e in batched_events
            ]
            events_with_random_time.sort(key=lambda x: x[0])
        elif ORDER == "time":
            # When writing tests it can be convenient to have events arrive in a more well-defined and logical order.
            # Note that stripe can still mess things up. E.g. 'updated' events may have a timestamp that is before the
            # 'created' event. But it's likely that they are at least mostly in the right order.
            events_with_random_time = [(int(e["created"]), e) for e in batched_events]
            events_with_random_time.sort(key=lambda x: x[0])

        for _, ev in events_with_random_time:
            stripe_event.stripe_event(ev, current_time=event_semantic_time(ev))

    def test_subscriptions_create1(self) -> None:
        """
        Checks that a subscription is started for new members.
        """
        (now, clock, member_id) = self.setup_single_member()

        assert not get_membership_summary(member_id).membership_active

        subscription_schedule_id = stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.MEMBERSHIP,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        self.advance_clock(clock, now + relativedelta(days=1))

        summary = get_membership_summary(member_id, clock.date)
        assert summary.membership_active
        # Note: Uses relativedelta to be able to handle leap years.
        assert summary.membership_end == (now + relativedelta(years=1)).date()

    def test_subscriptions_create2(self) -> None:
        """
        Checks that a subscription is scheduled when a member is already a member.
        """
        (now, clock, member_id) = self.setup_single_member()

        assert not get_membership_summary(member_id).membership_active
        # Add a span to ensure the subscription cannot start immediately
        self.add_span(
            self.get_member(member_id),
            Span.MEMBERSHIP,
            now.date(),
            (now + relativedelta(days=10)).date(),
        )

        subscription_schedule_id = stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.MEMBERSHIP,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        self.advance_clock(clock, now + relativedelta(days=1))

        # Note that the scheduled subscription is not the same as the real subscription.
        assert (
            self.get_member(member_id).stripe_membership_subscription_id
            == subscription_schedule_id
        ), "The member should have a scheduled subscription"

        self.advance_clock(clock, now + relativedelta(days=11))

        summary = get_membership_summary(member_id, clock.date)
        assert summary.membership_active
        # Note: Uses relativedelta to be able to handle leap years.
        assert summary.membership_end == (now + relativedelta(years=1, days=10)).date()

        subscription_id = self.get_member(member_id).stripe_membership_subscription_id
        # The real subscription should have started now, which has a different ID from the scheduled subscription.
        assert subscription_id is not None
        assert subscription_id != subscription_schedule_id

    def test_subscriptions_renewal(self) -> None:
        """
        Checks that a subscription is renewed properly, and that cancelling it stops automatic renewal.
        """
        (now, clock, member_id) = self.setup_single_member()

        assert not get_membership_summary(member_id).membership_active

        subscription_schedule_id = stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.MEMBERSHIP,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        
        # Note that the scheduled subscription is not the same as the real subscription.
        assert (
            self.get_member(member_id).stripe_membership_subscription_id
            == subscription_schedule_id
        ), "The member should have a scheduled subscription"

        self.advance_clock(clock, now + relativedelta(days=11))

        # Check that the subscription was started correctly
        subscription_id = self.get_member(member_id).stripe_membership_subscription_id
        assert subscription_id != subscription_schedule_id
        summary = get_membership_summary(member_id, clock.date)
        assert summary.membership_active
        assert summary.membership_end == (now + relativedelta(years=1)).date()

        self.advance_clock(clock, now + relativedelta(years=1, days=5))

        # Check that the subscription was renewed
        assert (
            self.get_member(member_id).stripe_membership_subscription_id
            == subscription_id
        )
        summary = get_membership_summary(member_id, clock.date)
        assert summary.membership_active
        assert summary.membership_end == (now + relativedelta(years=2)).date()

        was_cancelled = stripe_checkout.cancel_subscription(
            member_id, SubscriptionType.MEMBERSHIP, test_clock=clock.stripe_clock
        )
        assert was_cancelled

        # Check that the membership is still active until the end of the current membership period.
        # Even stripe's subscription remains active until the end of the current period.
        assert (
            self.get_member(member_id).stripe_membership_subscription_id
            == subscription_id
        )
        self.advance_clock(clock, now + relativedelta(years=1, days=6))
        summary = get_membership_summary(member_id, clock.date)
        assert summary.membership_active
        assert summary.membership_end == (now + relativedelta(years=2)).date()

        # Check that the subscription was not renewed
        self.advance_clock(clock, now + relativedelta(years=2, days=5))
        summary = get_membership_summary(member_id, clock.date)
        assert not summary.membership_active
        assert self.get_member(member_id).stripe_membership_subscription_id is None

    def test_subscriptions_cancel_scheduled(self) -> None:
        """
        Checks that a subscription can be cancelled before it even started.
        """
        (now, clock, member_id) = self.setup_single_member()

        # Add a span to ensure the subscription cannot start immediately
        self.add_span(
            self.get_member(member_id),
            Span.MEMBERSHIP,
            now.date(),
            (now + relativedelta(days=10)).date(),
        )
        assert get_membership_summary(member_id, clock.date).membership_active

        stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.MEMBERSHIP,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )

        self.advance_clock(clock, now + relativedelta(days=4))

        was_cancelled = stripe_checkout.cancel_subscription(
            member_id, SubscriptionType.MEMBERSHIP, test_clock=clock.stripe_clock
        )
        assert was_cancelled

        self.advance_clock(clock, now + relativedelta(days=6))

        # Check that the membership is still active until the end of the current membership period.
        # The scripe subscription should be cancelled.
        assert self.get_member(member_id).stripe_membership_subscription_id is None

        summary = get_membership_summary(member_id, clock.date)
        assert summary.membership_active
        assert summary.membership_end == (now + relativedelta(days=10)).date()

        self.advance_clock(clock, now + relativedelta(days=20))

        # Ensure the subscription didn't start
        assert self.get_member(member_id).stripe_membership_subscription_id is None
        summary = get_membership_summary(member_id, clock.date)
        assert not summary.membership_active

    def test_subscriptions_member_deleted(self) -> None:
        """
        Checks that if a member is deleted, their subscription is cancelled and the stripe customer is deleted
        """
        (now, clock, member_id) = self.setup_single_member()

        stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.MEMBERSHIP,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        stripe_customer_id = self.get_member(member_id).stripe_customer_id

        self.advance_clock(clock, now + relativedelta(days=4))

        membership.views.member_entity.delete(member_id, commit=True)

        self.advance_clock(clock, now + relativedelta(days=6))

        assert self.get_member(member_id).deleted_at is not None
        assert stripe.Customer.retrieve(stripe_customer_id).deleted

    def test_subscriptions_binding_period(self) -> None:
        """
        Checks that a lab subscription is started with a binding period
        """
        binding_period = BINDING_PERIOD[SubscriptionType.LAB]
        if binding_period <= 0:
            pytest.skip("No binding period for lab access")

        (now, clock, member_id) = self.setup_single_member()

        stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.LAB,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        self.advance_clock(clock, now + relativedelta(days=1))

        summary = get_membership_summary(member_id, clock.date)
        assert summary.labaccess_active
        assert (
            summary.labaccess_end == (now + relativedelta(months=binding_period)).date()
        )

        self.advance_clock(clock, now + relativedelta(months=1, days=5))

        # Ensure the subscription does not bill again after only one month.
        # It should start billing again only after the binding period has passed.
        summary = get_membership_summary(member_id, clock.date)
        assert summary.labaccess_active
        assert (
            summary.labaccess_end == (now + relativedelta(months=binding_period)).date()
        )

        self.advance_clock(clock, now + relativedelta(months=2, days=5))

        # After the binding period, the subscription should be renewed
        summary = get_membership_summary(member_id, clock.date)
        assert summary.labaccess_active
        assert (
            summary.labaccess_end
            == (now + relativedelta(months=binding_period + 1)).date()
        )

    def test_subscriptions_resubscribe(self) -> None:
        """
        Checks that a subscription can be cancelled, and the member can resubscribe immediately
        """
        binding_period = BINDING_PERIOD[SubscriptionType.LAB]
        if binding_period <= 0:
            pytest.skip("No binding period for lab access")

        (now, clock, member_id) = self.setup_single_member()

        stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.LAB,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        self.advance_clock(clock, now + relativedelta(days=1))

        # Cancel subscription after one day
        stripe_checkout.cancel_subscription(
            member_id, SubscriptionType.LAB, test_clock=clock.stripe_clock
        )
        # And immediately regret that decision and resubscribe (which is only proper)
        stripe_checkout.start_subscription(
            member_id, SubscriptionType.LAB, test_clock=clock.stripe_clock
        )

        self.advance_clock(clock, now + relativedelta(days=1))

        summary = get_membership_summary(member_id, clock.date)
        assert (
            summary.labaccess_end == (now + relativedelta(months=binding_period)).date()
        )

        # Stripe does not allow us to advance clocks more than 2 subscription-periods at once
        # So we have to do this in steps.
        for month in range(binding_period):
            self.advance_clock(clock, now + relativedelta(months=month + 1))

        self.advance_clock(clock, now + relativedelta(months=binding_period, days=5))

        # After the binding period of the first subscription finishes, the second subscription should start.
        # The second subscription shouldn't have a binding period because they were already members when the second
        # subscription was scheduled.
        summary = get_membership_summary(member_id, clock.date)
        assert (
            summary.labaccess_end
            == (now + relativedelta(months=binding_period + 1)).date()
        )

    def test_subscriptions_failing_card(self) -> None:
        """
        Checks that if a subscription fails to charge, the subscription is deleted after a while
        """
        binding_period = BINDING_PERIOD[SubscriptionType.LAB]
        if binding_period <= 0:
            pytest.skip("No binding period for lab access")

        (now, clock, member_id) = self.setup_single_member()

        stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.MEMBERSHIP,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        self.advance_clock(clock, now + relativedelta(days=1))

        summary = get_membership_summary(member_id, clock.date)
        assert (
            summary.membership_active
        ), "The subscription was paid with a valid card the first time, so the member should have active membership"

        self.set_payment_method(
            self.get_member(member_id), DECLINE_AFTER_ATTACHING_CARD, clock
        )

        # Stripe should be configured to retry the payment 3 times before giving up
        # This will take 3 + 5 + 7 = 15 days with the default settings
        self.advance_clock(clock, now + relativedelta(years=1, days=16))

        summary = get_membership_summary(member_id, clock.date)
        assert (
            not summary.membership_active
        ), "The subscription was not paid, so the member should not have active membership"
        assert (
            self.get_member(member_id).stripe_membership_subscription_id is None
        ), "The subscription should have been cancelled at this point"

    def test_subscriptions_retry_card(self) -> None:
        """
        Checks that if a subscription fails to charge, the subscription is retried a few times and then nenewed when we switch to a new card
        """
        binding_period = BINDING_PERIOD[SubscriptionType.LAB]
        if binding_period <= 0:
            pytest.skip("No binding period for lab access")

        (now, clock, member_id) = self.setup_single_member()

        stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.MEMBERSHIP,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        self.advance_clock(clock, now + relativedelta(days=1))

        summary = get_membership_summary(member_id, clock.date)
        assert (
            summary.membership_active
        ), "The subscription was paid with a valid card the first time, so the member should have active membership"

        self.set_payment_method(
            self.get_member(member_id), DECLINE_AFTER_ATTACHING_CARD, clock
        )

        # Stripe should be configured to retry the payment 3 times before giving up
        # This will take 3 + 5 + 7 = 15 days with the default settings
        self.advance_clock(clock, now + relativedelta(years=1, days=2))

        # Restore a valid payment method. The card will be retried at 1year + 3days
        self.set_payment_method(self.get_member(member_id), VALID_3DS_CARD_NO, clock)

        self.advance_clock(clock, now + relativedelta(years=1, days=10))

        summary = get_membership_summary(member_id, clock.date)
        assert (
            summary.membership_active
        ), "The subscription was paid, so the member should have active membership"
        # When the card is retried, the subscription should be renewed for another year.
        # This behavior is slightly different to what will happen in reality.
        # In reality, the subscription will be renewed at 1year+3days because
        # that's when stripe checks the card again, and then we will add new membership to the member from that time.
        # But since we are faking times during the test, the behavior is not 100% truthful.
        # But this is close enough to verify that everything works as expected.
        assert summary.membership_end == (now + relativedelta(years=2)).date()
        assert (
            self.get_member(member_id).stripe_membership_subscription_id is not None
        ), "The subscription should not have been deleted"
    
    def test_subscriptions_signed_agreement1(self) -> None:
        """
        Checks that labaccess is not granted if the member has not signed the agreement.
        The subscription is immediatelly paused, and only resumed when the member signs the agreement.
        In this variant the member signs the agreement after just a few days.
        """
        (now, clock, member_id) = self.setup_single_member(signed_labaccess=False)

        assert not get_membership_summary(member_id).membership_active

        subscription_schedule_id = stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.LAB,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        
        self.advance_clock(clock, now + relativedelta(days=5))

        summary = get_membership_summary(member_id, clock.date)
        assert not summary.labaccess_active
        
        # Member signs agreement
        self.get_member(member_id).labaccess_agreement_at = clock.date
        db_session.commit()
        # Ship any orders related to the member. We exclude all other members
        # because that might mess up other tests running in parallel.
        ship_orders(True, current_time=clock.date, member_id=member_id)

        self.advance_clock(clock, now + relativedelta(days=5))

        summary = get_membership_summary(member_id, clock.date)
        assert summary.labaccess_active
        assert summary.labaccess_end == (now + relativedelta(months=2, days=5)).date()

        # Stripe limits how much we can advance the clock in one go
        self.advance_clock(clock, now + relativedelta(months=2, days=3))
        self.advance_clock(clock, now + relativedelta(months=2, days=5))

        summary = get_membership_summary(member_id, clock.date)
        assert summary.labaccess_active
        assert summary.labaccess_end == (now + relativedelta(months=3, days=5)).date()
    
    def test_subscriptions_signed_agreement2(self) -> None:
        """
        Checks that labaccess is not granted if the member has not signed the agreement.
        The subscription is immediatelly paused, and only resumed when the member signs the agreement.
        In this variant the member signs the agreement after binding period would have been over.
        """
        (now, clock, member_id) = self.setup_single_member(signed_labaccess=False)

        assert not get_membership_summary(member_id).membership_active

        stripe_checkout.start_subscription(
            member_id,
            SubscriptionType.LAB,
            earliest_start_at=now,
            test_clock=clock.stripe_clock,
        )
        
        self.advance_clock(clock, now + relativedelta(months=1, days=5))

        # Since the member has not signed the agreement yet, they should not have labaccess
        summary = get_membership_summary(member_id, clock.date)
        assert not summary.labaccess_active

        self.advance_clock(clock, now + relativedelta(months=2, days=5))
        self.advance_clock(clock, now + relativedelta(months=3, days=5))

        # Member signs agreement after more than 3 months
        # Their 2 months of initial labaccess will start ticking now
        self.get_member(member_id).labaccess_agreement_at = clock.date
        db_session.commit()
        ship_orders(True, current_time=clock.date, member_id=member_id)

        self.advance_clock(clock, now + relativedelta(months=3, days=10))

        summary = get_membership_summary(member_id, clock.date)
        assert summary.labaccess_active
        assert summary.labaccess_end == (now + relativedelta(months=5, days=5)).date()

        self.advance_clock(clock, now + relativedelta(months=5, days=6))

        # The member should now have finished their binding period and been billed for another month
        summary = get_membership_summary(member_id, clock.date)
        assert summary.labaccess_active
        assert summary.labaccess_end == (now + relativedelta(months=6, days=5)).date()
