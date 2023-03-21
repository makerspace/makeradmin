from datetime import date, timedelta, datetime, timezone
import time
import random
import copy
from typing import Any, Dict, Literal, Set
from unittest.mock import Mock, patch
from test_aid.systest_base import VALID_3DS_CARD_NO
from shop.stripe_checkout import SubscriptionType, get_stripe_customer
from shop import stripe_checkout
from shop.stripe_util import set_global_clock
from membership.membership import get_membership_summary
from test_aid.test_util import random_str
from membership.member_auth import hash_password
from test_aid.obj import ObjFactory, DEFAULT_PASSWORD
import core
import messages
import shop
from dispatch_emails import membership_reminder, MEMBERSHIP_REMINDER_DAYS_BEFORE, \
    MEMBERSHIP_REMINDER_GRACE_PERIOD
import membership
import membership.models
import shop.models
import messages.models
import core.models
from membership.models import Span, Member
from messages.models import Message, MessageTemplate
from service.db import db_session
from shop.models import ProductAction, Transaction
from shop.transactions import create_transaction
from test_aid.test_base import FlaskTestBase, ShopTestMixin
import stripe
from shop import stripe_event
from shop import stripe_constants


class FakeClock:
    def __init__(self, date: datetime) -> None:
        self.date = date
        self.stripe_clock = stripe.test_helpers.TestClock.create(frozen_time=int(date.timestamp()), name="TestClock")

    def set_as_global(self) -> None:
        set_global_clock(self.stripe_clock)

    def advance(self, to: datetime) -> None:
        assert to >= self.date
        self.date = to
        stripe.test_helpers.TestClock.advance(self.stripe_clock.stripe_id, frozen_time=int(self.date.timestamp()))


class Test(FlaskTestBase):

    models = [membership.models, messages.models, shop.models, core.models]
    seen_event_ids: Set[str]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Span).delete()
        db_session.query(Message).delete()
        self.seen_event_ids = set()
        stripe_constants.set_stripe_key(True)

    def tearDown(self) -> None:
        set_global_clock(None)
        # for c in stripe.test_helpers.TestClock.list():
        #     stripe.test_helpers.TestClock.delete(c)
        return super().tearDown()

    def add_span(self, member: Member, type: str, startdate: date, enddate: date) -> None:
        span = Span(startdate=startdate, enddate=enddate, type=type, member=member, creation_reason=random_str())
        db_session.add(span)
        db_session.commit()

    def advance_clock(self, clock: FakeClock, time: datetime) -> None:
        t0 = clock.date
        clock.advance(to=time)
        self.poll_stripe_events(t0, "test_helpers.test_clock.ready")

    def poll_stripe_events(self, min_time: datetime, until_seen_type: str) -> None:
        batched_events = []
        done = False
        print("Waiting for stripe events...")
        while not done:
            time.sleep(0.1)
            events = stripe.Event.list(created={"gte": int(min_time.timestamp())})
            for ev in events:
                if ev.id in self.seen_event_ids:
                    continue

                self.seen_event_ids.add(ev.stripe_id)
                batched_events.append(ev)
                if ev.type == until_seen_type:
                    done = True
                    break
        
        ORDER = 'time'

        if ORDER == 'random':
            # Stripe webhook events do not guarantee that they arrive in any particular order.
            # To emulate this, we sort the events based on their time with a random perturbation.
            # This will make sure that the api is not sensitive to the precise order of events.
            MAX_OFFSET_SECONDS = 30
            events_with_random_time = [((int(e["created"]) + random.randint(-MAX_OFFSET_SECONDS, MAX_OFFSET_SECONDS)), e) for e in batched_events]
            events_with_random_time.sort(key=lambda x: x[0])
        elif ORDER == 'time':
            # When writing tests it can be convenient to have events arrive in a more well-defined and logical order.
            # Note that stripe can still mess things up. E.g. 'updated' events may have a timestamp that is before the
            # 'created' event. But it's likely that they are at least mostly in the right order.
            events_with_random_time = [(int(e["created"]), e) for e in batched_events]
            events_with_random_time.sort(key=lambda x: x[0])
        
        for _, ev in events_with_random_time:
            stripe_event.stripe_event(ev)

    @staticmethod
    def card(number: str) -> Dict[str, Any]:
        return {
            "number": number,
            "exp_month": 12,
            "exp_year": 2030,
            "cvc": '123'
        }

    def create_member_that_can_pay(self) -> Member:
        member = self.db.create_member(password=hash_password(DEFAULT_PASSWORD))

        payment_method = stripe.PaymentMethod.create(type="card", card=self.card(VALID_3DS_CARD_NO))
        stripe_member = get_stripe_customer(member)
        assert stripe_member is not None
        stripe.PaymentMethod.attach(payment_method, customer=stripe_member.stripe_id)
        stripe.Customer.modify(stripe_member.stripe_id, invoice_settings={
            'default_payment_method': payment_method.stripe_id,
        })
        return member

    def test_subscriptions1(self) -> None:
        now = datetime.now(timezone.utc)
        clock = FakeClock(now)
        clock.set_as_global()
        member = self.create_member_that_can_pay()

        assert not get_membership_summary(member.member_id).membership_active
        self.add_span(member, Span.MEMBERSHIP, now.date(), (now + timedelta(days=10)).date())

        subscription = stripe_checkout.start_subscription(member.member_id, SubscriptionType.MEMBERSHIP, start_at=now)
        self.advance_clock(clock, now + timedelta(days=11))

        summary = get_membership_summary(member.member_id, clock.date)
        assert summary.membership_active
        assert summary.membership_end == (now + timedelta(days=365 + 10 + 1)).date()
    
    # def test_subscriptions_renewal(self) -> None:
    #     now = datetime.now(timezone.utc)
    #     clock = FakeClock(now)
    #     clock.set_as_global()
    #     member = self.create_member_that_can_pay()

    #     assert not get_membership_summary(member.member_id).membership_active

    #     subscription = stripe_checkout.start_subscription(member.member_id, SubscriptionType.MEMBERSHIP, start_at=now)
    #     self.advance_clock(clock, now + timedelta(days=11))

    #     summary = get_membership_summary(member.member_id, clock.date)
    #     assert summary.membership_active
    #     assert summary.membership_end == (now + timedelta(days=366)).date()

    #     self.advance_clock(clock, now + timedelta(days=370))

    #     summary = get_membership_summary(member.member_id, clock.date)
    #     assert summary.membership_active
    #     assert summary.membership_end == (now + timedelta(days=366 + 366)).date()
        
    
    #
    # If a member has a subscription, and they buy a one-off monthly/yearly membership, the subscription should be cancelled
    # This should ideally show a confirmation pop-up in the webshop.
    #
    # If a subscription is started, it is also renewed automatically.
    #
    # If a member starts a subscription without being a member, they should become membership members from today.
    # But lab membership subscription should only start after they have signed the lab agreement.
    #
    # If a member starts a subscription while being a member, the subscription should start from the end of the current membership.
    #
    # If a subscription runs for more than two months, the price should be reduced
    #
    # Check invariants after every step

