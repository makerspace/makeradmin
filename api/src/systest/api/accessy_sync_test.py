import re
from datetime import date

from membership.models import Span
from multiaccessy.accessy import AccessyMember, ACCESSY_LABACCESS_GROUP, ACCESSY_SPECIAL_LABACCESS_GROUP
from multiaccessy.sync import get_wanted_access, calculate_diff, Diff, GroupOp
from test_aid.obj import random_phone_number
from test_aid.systest_base import ApiTest


class Test(ApiTest):

    def test_diff(self):
        m1_phone = random_phone_number()
        m1_both = AccessyMember(phone=m1_phone, groups={ACCESSY_SPECIAL_LABACCESS_GROUP, ACCESSY_LABACCESS_GROUP})
        m1_lab = AccessyMember(phone=m1_phone, groups={ACCESSY_LABACCESS_GROUP})
        m1_special = AccessyMember(phone=m1_phone, groups={ACCESSY_SPECIAL_LABACCESS_GROUP})
        m1_none = AccessyMember(phone=m1_phone, groups=set())

        diff = calculate_diff(wanted_members={m1_phone: m1_both}, actual_members={})
        self.assertEqual(Diff(invites=[m1_both]), diff)

        diff = calculate_diff(wanted_members={m1_phone: m1_lab}, actual_members={m1_phone: m1_both})
        self.assertEqual(Diff(group_removes=[GroupOp(m1_both, ACCESSY_SPECIAL_LABACCESS_GROUP)]), diff)

        diff = calculate_diff(wanted_members={m1_phone: m1_lab}, actual_members={m1_phone: m1_none})
        self.assertEqual(Diff(group_adds=[GroupOp(m1_lab, ACCESSY_LABACCESS_GROUP)]), diff)

        diff = calculate_diff(wanted_members={}, actual_members={m1_phone: m1_none})
        self.assertEqual(Diff(org_removes=[m1_none]), diff)

        diff = calculate_diff(wanted_members={m1_phone: m1_lab}, actual_members={m1_phone: m1_special})
        self.assertEqual(Diff(group_adds=[GroupOp(m1_lab, ACCESSY_LABACCESS_GROUP)], group_removes=[GroupOp(m1_special, ACCESSY_SPECIAL_LABACCESS_GROUP)]), diff)

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
        self.assertIn(ACCESSY_SPECIAL_LABACCESS_GROUP, wanted[included_because_special_span.phone].groups)

        self.assertIn(included_because_labaccess_span.member_id, wanted_ids)
        self.assertIn(included_because_labaccess_span.phone, wanted)
        self.assertIn(ACCESSY_LABACCESS_GROUP, wanted[included_because_labaccess_span.phone].groups)

        self.assertIn(included_because_both_kinds_of_spans.member_id, wanted_ids)
        self.assertIn(included_because_both_kinds_of_spans.phone, wanted)
        self.assertIn(ACCESSY_LABACCESS_GROUP, wanted[included_because_both_kinds_of_spans.phone].groups)
        self.assertIn(ACCESSY_SPECIAL_LABACCESS_GROUP, wanted[included_because_both_kinds_of_spans.phone].groups)

        self.assertNotIn(not_included_because_spans_outside_today.member_id, wanted_ids)
        self.assertNotIn(not_included_because_spans_outside_today.phone, wanted)

        self.assertNotIn(not_included_because_labaccess_agreement_not_signed.member_id, wanted_ids)
        self.assertNotIn(not_included_because_labaccess_agreement_not_signed.phone, wanted)

        self.assertNotIn(not_included_because_no_phone_number.member_id, wanted_ids)
        self.assertNotIn(not_included_because_no_phone_number.phone, wanted)

        self.assertNotIn(not_included_because_deleted.member_id, wanted_ids)
        self.assertNotIn(not_included_because_deleted.phone, wanted)


