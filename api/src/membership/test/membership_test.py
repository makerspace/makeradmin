from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from datetime import datetime as dt
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar

import core
import core.models
import membership
import membership.models
import membership.views
import messages
import messages.models
import shop
import shop.models
from membership.membership import get_membership_summaries
from membership.models import Member, Span
from test_aid.test_base import FlaskTestBase, ShopTestMixin


class MembershipTest(ShopTestMixin, FlaskTestBase):
    models = [membership.models, messages.models, shop.models, core.models]

    def test_get_membership_summaries_labbaccess_has_ended(self):
        fixed_now = date(2024, 10, 1)
        start = fixed_now - timedelta(days=10)
        membership_end = fixed_now + timedelta(days=200)
        lab_access_end_date = fixed_now - timedelta(days=10)

        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, startdate=start, enddate=membership_end)
        self.db.create_span(type=Span.LABACCESS, startdate=start, enddate=lab_access_end_date)

        membership_datas = get_membership_summaries([member.member_id], fixed_now)

        self.assertEqual(len(membership_datas), 1)
        summary = membership_datas[0]

        self.assertTrue(summary.membership_active)
        self.assertEqual(summary.membership_end, membership_end)

        self.assertFalse(summary.labaccess_active)
        self.assertEqual(summary.labaccess_end, lab_access_end_date)

        self.assertFalse(summary.special_labaccess_active)
        self.assertIsNone(summary.special_labaccess_end)

        self.assertFalse(summary.effective_labaccess_active)
        self.assertEqual(summary.effective_labaccess_end, lab_access_end_date)

    def test_get_membership_summaries_labaccess_ends_in_the_future(self):
        fixed_now = date(2024, 10, 1)
        start = fixed_now - timedelta(days=10)
        membership_end = fixed_now + timedelta(days=200)
        lab_access_end_date = fixed_now + timedelta(days=10)

        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, startdate=start, enddate=membership_end)
        self.db.create_span(type=Span.LABACCESS, startdate=start, enddate=lab_access_end_date)

        membership_datas = get_membership_summaries([member.member_id], fixed_now)

        self.assertEqual(len(membership_datas), 1)
        summary = membership_datas[0]

        self.assertTrue(summary.membership_active)
        self.assertEqual(summary.membership_end, membership_end)

        self.assertTrue(summary.labaccess_active)
        self.assertEqual(summary.labaccess_end, lab_access_end_date)

        self.assertFalse(summary.special_labaccess_active)
        self.assertIsNone(summary.special_labaccess_end)

        self.assertTrue(summary.effective_labaccess_active)
        self.assertEqual(summary.effective_labaccess_end, lab_access_end_date)

    def test_get_membership_summaries_labaccess_ends_today(self):
        fixed_now = date(2024, 10, 1)
        start = fixed_now - timedelta(days=10)
        membership_end = fixed_now + timedelta(days=200)
        lab_access_end_date = fixed_now

        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, startdate=start, enddate=membership_end)
        self.db.create_span(type=Span.LABACCESS, startdate=start, enddate=lab_access_end_date)

        membership_datas = get_membership_summaries([member.member_id], fixed_now)

        self.assertEqual(len(membership_datas), 1)
        summary = membership_datas[0]

        self.assertTrue(summary.membership_active)
        self.assertEqual(summary.membership_end, membership_end)

        self.assertTrue(summary.labaccess_active)
        self.assertEqual(summary.labaccess_end, lab_access_end_date)

        self.assertFalse(summary.special_labaccess_active)
        self.assertIsNone(summary.special_labaccess_end)

        self.assertTrue(summary.effective_labaccess_active)
        self.assertEqual(summary.effective_labaccess_end, lab_access_end_date)
