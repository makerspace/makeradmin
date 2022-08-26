import re
from datetime import date

from membership.models import Span
from multiaccessy.sync import get_wanted_access
from test_aid.obj import random_phone_number
from test_aid.systest_base import ApiTest


class Test(ApiTest):

    def test_get_wanted_access(self):
        included_because_labaccess_span = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(startdate=self.date(-1), enddate=self.date(0), type=Span.LABACCESS)

        included_because_special_span = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(startdate=self.date(0), enddate=self.date(1), type=Span.SPECIAL_LABACESS)

        included_because_both_kinds_of_spans = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(startdate=self.date(0), enddate=self.date(0), type=Span.LABACCESS)
        self.db.create_span(startdate=self.date(0), enddate=self.date(0), type=Span.SPECIAL_LABACESS)

        not_included_because_spans_outside_today = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(startdate=self.date(-1), enddate=self.date(-1), type=Span.LABACCESS)
        self.db.create_span(startdate=self.date(1), enddate=self.date(1), type=Span.LABACCESS)

        not_included_because_labaccess_agreement_not_signed = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=None,
        )
        self.db.create_span(startdate=self.date(0), enddate=self.date(0), type=Span.LABACCESS)

        not_included_because_no_phone_number = self.db.create_member(
            phone=None,
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(startdate=self.date(0), enddate=self.date(0), type=Span.LABACCESS)

        not_included_because_deleted = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
            deleted_at=self.datetime(),
        )
        self.db.create_span(startdate=self.date(0), enddate=self.date(0), type=Span.LABACCESS)

        wanted = get_wanted_access(self.date())
        
        wanted_ids = {m.member_id for m in wanted.values()}
        
        self.assertIn(included_because_special_span.member_id, wanted_ids)
        self.assertIn(included_because_special_span.phone, wanted)

        self.assertIn(included_because_labaccess_span.member_id, wanted_ids)
        self.assertIn(included_because_labaccess_span.phone, wanted)

        self.assertIn(included_because_both_kinds_of_spans.member_id, wanted_ids)
        self.assertIn(included_because_both_kinds_of_spans.phone, wanted)

        self.assertNotIn(not_included_because_spans_outside_today.member_id, wanted_ids)
        self.assertNotIn(not_included_because_spans_outside_today.phone, wanted)

        self.assertNotIn(not_included_because_labaccess_agreement_not_signed.member_id, wanted_ids)
        self.assertNotIn(not_included_because_labaccess_agreement_not_signed.phone, wanted)

        self.assertNotIn(not_included_because_no_phone_number.member_id, wanted_ids)
        self.assertNotIn(not_included_because_no_phone_number.phone, wanted)

        self.assertNotIn(not_included_because_deleted.member_id, wanted_ids)
        self.assertNotIn(not_included_because_deleted.phone, wanted)


