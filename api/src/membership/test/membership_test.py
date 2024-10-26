from dataclasses import dataclass
from datetime import date, timedelta, timezone
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

    def test_get_membership_summaries_old(self):
        membership_end = self.date(200)
        lab_access_end_date = self.date(-10)

        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=membership_end)
        self.db.create_span(type=Span.LABACCESS, enddate=lab_access_end_date)

        membership_datas = get_membership_summaries([member.member_id])

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

    def test_get_membership_summaries_future(self):
        membership_end = self.date(200)
        lab_access_end_date = self.date(10)

        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=membership_end)
        self.db.create_span(type=Span.LABACCESS, enddate=lab_access_end_date)

        membership_datas = get_membership_summaries([member.member_id])

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

    def test_get_membership_summaries_today(self):
        membership_end = self.date(200)
        lab_access_end_date = self.date()

        member = self.db.create_member()
        self.db.create_span(type=Span.MEMBERSHIP, enddate=membership_end)
        self.db.create_span(type=Span.LABACCESS, enddate=lab_access_end_date)

        membership_datas = get_membership_summaries([member.member_id])

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
