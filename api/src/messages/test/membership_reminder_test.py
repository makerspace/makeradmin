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


class Test(ShopTestMixin, FlaskTestBase):
    
    models = [membership.models, messages.models, shop.models, core.models]
    products = [
        dict(
            price=100.0,
            unit="st",
            smallest_multiple=1,
            action=dict(action_type=ProductAction.ADD_MEMBERSHIP_DAYS, value=30)
        )
    ]

    def setUp(self) -> None:
        db_session.query(Member).delete()
        db_session.query(Span).delete()
        db_session.query(Message).delete()
    
    def send_membership(self) -> None:
        membership_reminder()
        db_session.commit()

    def test_reminder_message_is_created_20_days_before_expiry(self) -> None:
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE))
        
        self.send_membership()
        
        message, = db_session.query(Message).all()
        
        self.assertEqual(member.member_id, message.member_id)
        self.assertEqual(MessageTemplate.MEMBERSHIP_REMINDER.value, message.template)
    
    def test_reminder_message_is_not_created_if_membership_active(self) -> None:
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE + 20))
        
        self.send_membership()
        
        self.assertEqual(0, db_session.query(Message).filter(Message.member == member).count())

    def test_reminder_message_is_created_20_days_before_expiry_even_if_other_span_after(self) -> None:
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE))
        self.db.create_span(type=Span.LABACCESS, enddate=self.date(200))
        
        self.send_membership()
        
        self.assertEqual(1, db_session.query(Message).filter(Message.member == member).count())
        
    def test_reminder_message_is_not_created_if_recent_reminder_already_exists(self) -> None:
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE))
        self.db.create_message(
            template=MessageTemplate.MEMBERSHIP_REMINDER.value,
            member=member,
            created_at=self.datetime(days=-MEMBERSHIP_REMINDER_GRACE_PERIOD + 1),
        )
        
        self.send_membership()
        
        self.assertEqual(1, db_session.query(Message).filter(Message.member == member).count())

    def test_reminder_message_is_created_if_recent_reminder_is_old(self) -> None:
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE))
        self.db.create_message(
            template=MessageTemplate.MEMBERSHIP_REMINDER.value,
            member=member,
            created_at=self.datetime(days=-MEMBERSHIP_REMINDER_GRACE_PERIOD - 2),
        )
        
        self.send_membership()
        
        self.assertEqual(2, db_session.query(Message).filter((Message.member == member) & (Message.template == MessageTemplate.MEMBERSHIP_REMINDER.value)).count())

    def test_reminder_message_is_created_if_member_got_other_message(self) -> None:
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE))
        self.db.create_message(
            template=MessageTemplate.BOX_TERMINATED.value,
            member=member,
            created_at=self.datetime(days=-1),
        )
        
        self.send_membership()
        
        self.assertEqual(1, db_session.query(Message).filter((Message.member == member) & (Message.template == MessageTemplate.MEMBERSHIP_REMINDER.value)).count())

    def test_reminder_message_is_created_if_member_another_member_got_recent_reminder(self) -> None:
        other_member = self.db.create_member()
        self.db.create_message(
            template=MessageTemplate.MEMBERSHIP_REMINDER.value,
            member=other_member,
            created_at=self.datetime(days=-1),
        )
        
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE))
        
        self.send_membership()
        
        self.assertEqual(1, db_session.query(Message).filter(Message.member == member).count())

    def test_reminder_message_is_not_created_if_member_has_pending_membership_days(self) -> None:
        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(MEMBERSHIP_REMINDER_DAYS_BEFORE))
        p0_count = 1

        expected_sum = self.p0_price * p0_count
        cart = [
            {"id": self.p0_id, "count": p0_count},
        ]

        transaction = create_transaction(member_id=member.member_id,
                                         purchase=dict(cart=cart, expected_sum=expected_sum),
                                         stripe_reference_id="not_used")
        transaction.status = Transaction.COMPLETED
        db_session.add(transaction)
        db_session.flush()

        self.send_membership()

        self.assertEqual(0, db_session.query(Message).count())
