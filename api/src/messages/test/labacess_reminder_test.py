
import messages
from dispatch_emails import labaccess_reminder, render_template, LABACCESS_REMINDER_DAYS_BEFORE, \
    LABACCESS_REMINDER_GRACE_PERIOD
from membership import membership
from membership.models import Span, Member
from messages.models import Message, MessageTemplate
from service.db import db_session
from test_aid.test_base import FlaskTestBase


class Test(FlaskTestBase):
    
    models = [membership.models, messages.models]

    def setUp(self):
        db_session.query(Member).delete()
        db_session.query(Span).delete()
        db_session.query(Message).delete()
    
    def test_reminder_message_is_created_20_days_before_expiry(self):
        member = self.db.create_member()
        self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        
        labaccess_reminder(db_session, render_template)
        
        message, = db_session.query(Message).all()
        
        self.assertEqual(member.member_id, message.member_id)
        self.assertEqual(MessageTemplate.LABACCESS_REMINDER.value, message.template)

    def test_reminder_message_is_created_20_days_before_expiry_even_if_other_span_after(self):
        member = self.db.create_member()
        self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(200))
        
        labaccess_reminder(db_session, render_template)
        
        self.assertEqual(1, db_session.query(Message).filter(Message.member == member).count())

    def test_reminder_message_is_not_created_unless_labaccess_and_20_days_before_expiry(self):
        m1 = self.db.create_member()
        s1 = self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE - 1))

        m2 = self.db.create_member()
        s2 = self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE + 1))

        m3 = self.db.create_member()
        s3 = self.db.create_span(type=Span.SPECIAL_LABACESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))

        m4 = self.db.create_member()
        s4 = self.db.create_span(type=Span.MEMBERSHIP, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))

        m5 = self.db.create_member()
        s5a = self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        s5b = self.db.create_span(type=Span.LABACCESS,
                                  startdate=self.date(LABACCESS_REMINDER_DAYS_BEFORE + 1),
                                  enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE +2))

        m6 = self.db.create_member()
        s6 = self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE),
                                 deleted_at=self.datetime())

        m7 = self.db.create_member(deleted_at=self.datetime())
        s7 = self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        
        labaccess_reminder(db_session, render_template)
        
        self.assertEqual(0, db_session.query(Message).count())
        
    def test_reminder_message_is_not_created_if_recent_reminder_already_exists(self):
        member = self.db.create_member()
        self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        self.db.create_message(
            template=MessageTemplate.LABACCESS_REMINDER.value,
            member=member,
            created_at=self.datetime(days=-LABACCESS_REMINDER_GRACE_PERIOD + 1),
        )
        
        labaccess_reminder(db_session, render_template)
        
        self.assertEqual(1, db_session.query(Message).filter(Message.member == member).count())

    def test_reminder_message_is_created_if_recent_reminder_is_old(self):
        member = self.db.create_member()
        self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        self.db.create_message(
            template=MessageTemplate.LABACCESS_REMINDER.value,
            member=member,
            created_at=self.datetime(days=-LABACCESS_REMINDER_GRACE_PERIOD - 2),
        )
        
        labaccess_reminder(db_session, render_template)
        
        self.assertEqual(2, db_session.query(Message).filter(Message.member == member).count())

    def test_reminder_message_is_created_if_member_got_other_message(self):
        member = self.db.create_member()
        self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        self.db.create_message(
            template=MessageTemplate.BOX_TERMINATED.value,
            member=member,
            created_at=self.datetime(days=-1),
        )
        
        labaccess_reminder(db_session, render_template)
        
        self.assertEqual(2, db_session.query(Message).filter(Message.member == member).count())

    def test_reminder_message_is_created_if_member_another_member_got_recent_reminder(self):
        other_member = self.db.create_member()
        self.db.create_message(
            template=MessageTemplate.LABACCESS_REMINDER.value,
            member=other_member,
            created_at=self.datetime(days=-1),
        )
        
        member = self.db.create_member()
        self.db.create_span(type=Span.LABACCESS, enddate=self.date(LABACCESS_REMINDER_DAYS_BEFORE))
        
        labaccess_reminder(db_session, render_template)
        
        self.assertEqual(1, db_session.query(Message).filter(Message.member == member).count())

    
