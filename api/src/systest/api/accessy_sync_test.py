import re
from datetime import date

from membership.models import Span
from multiaccessy.accessy import ACCESSY_LABACCESS_GROUP, ACCESSY_SPECIAL_LABACCESS_GROUP, AccessyMember
from multiaccessy.sync import Diff, GroupOp, calculate_diff, get_wanted_access
from service.db import db_session
from test_aid.obj import random_phone_number
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    def test_diff(self) -> None:
        self.assertIsNotNone(ACCESSY_SPECIAL_LABACCESS_GROUP)
        self.assertIsNotNone(ACCESSY_LABACCESS_GROUP)

        m1_phone = random_phone_number()
        m1_both = AccessyMember(phone=m1_phone, groups={ACCESSY_SPECIAL_LABACCESS_GROUP, ACCESSY_LABACCESS_GROUP})
        m1_lab = AccessyMember(phone=m1_phone, groups={ACCESSY_LABACCESS_GROUP})
        m1_special = AccessyMember(phone=m1_phone, groups={ACCESSY_SPECIAL_LABACCESS_GROUP})
        m1_none = AccessyMember(phone=m1_phone, groups=set())

        diff = calculate_diff(wanted={m1_phone: m1_both.groups}, actual={}, skip_attributes_for_added_items=True)
        self.assertEqual(Diff(item_adds=[m1_phone]), diff)

        diff = calculate_diff(wanted={m1_phone: m1_both.groups}, actual={}, skip_attributes_for_added_items=False)
        self.assertEqual(
            Diff(
                item_adds=[m1_phone],
                attribute_adds=[(m1_phone, ACCESSY_SPECIAL_LABACCESS_GROUP), (m1_phone, ACCESSY_LABACCESS_GROUP)],
            ),
            diff,
        )

        diff = calculate_diff(
            wanted={m1_phone: m1_lab.groups}, actual={m1_phone: m1_both.groups}, skip_attributes_for_added_items=True
        )
        self.assertEqual([(m1_both.phone, ACCESSY_SPECIAL_LABACCESS_GROUP)], diff.attribute_removes)
        self.assertEqual(Diff(attribute_removes=[(m1_both.phone, ACCESSY_SPECIAL_LABACCESS_GROUP)]), diff)

        diff = calculate_diff(
            wanted={m1_phone: m1_lab.groups}, actual={m1_phone: m1_none.groups}, skip_attributes_for_added_items=True
        )
        self.assertEqual(Diff(attribute_adds=[(m1_none.phone, ACCESSY_LABACCESS_GROUP)]), diff)

        diff = calculate_diff(wanted={}, actual={m1_phone: m1_none.groups}, skip_attributes_for_added_items=True)
        self.assertEqual(Diff(item_removes=[m1_none.phone]), diff)

        diff = calculate_diff(
            wanted={m1_phone: m1_lab.groups}, actual={m1_phone: m1_special.groups}, skip_attributes_for_added_items=True
        )
        self.assertEqual(
            Diff(
                attribute_adds=[(m1_special.phone, ACCESSY_LABACCESS_GROUP)],
                attribute_removes=[(m1_special.phone, ACCESSY_SPECIAL_LABACCESS_GROUP)],
            ),
            diff,
        )

    def test_get_wanted_access(self) -> None:
        included_because_labaccess_span = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(
            startdate=self.date(-1), enddate=self.date(0), type=Span.LABACCESS, member=included_because_labaccess_span
        )

        included_because_special_span = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(
            startdate=self.date(0),
            enddate=self.date(1),
            type=Span.SPECIAL_LABACESS,
            member=included_because_special_span,
        )

        included_because_both_kinds_of_spans = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(
            startdate=self.date(0),
            enddate=self.date(0),
            type=Span.LABACCESS,
            member=included_because_both_kinds_of_spans,
        )
        self.db.create_span(
            startdate=self.date(0),
            enddate=self.date(0),
            type=Span.SPECIAL_LABACESS,
            member=included_because_both_kinds_of_spans,
        )

        not_included_because_spans_outside_today = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(
            startdate=self.date(-1),
            enddate=self.date(-1),
            type=Span.LABACCESS,
            member=not_included_because_spans_outside_today,
        )
        self.db.create_span(
            startdate=self.date(1),
            enddate=self.date(1),
            type=Span.LABACCESS,
            member=not_included_because_spans_outside_today,
        )

        included_even_if_labaccess_agreement_not_signed = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=None,
        )
        self.db.create_span(
            startdate=self.date(0),
            enddate=self.date(0),
            type=Span.LABACCESS,
            member=included_even_if_labaccess_agreement_not_signed,
        )

        not_included_because_no_phone_number = self.db.create_member(
            phone=None,
            labaccess_agreement_at=date.today(),
        )
        self.db.create_span(
            startdate=self.date(0),
            enddate=self.date(0),
            type=Span.LABACCESS,
            member=not_included_because_no_phone_number,
        )

        not_included_because_deleted = self.db.create_member(
            phone=random_phone_number(),
            labaccess_agreement_at=date.today(),
            deleted_at=self.datetime(),
        )
        self.db.create_span(
            startdate=self.date(0), enddate=self.date(0), type=Span.LABACCESS, member=not_included_because_deleted
        )
        group = self.db.create_group(name="Test Group")
        TEST_GROUP_GUID = "test-group-guid"
        group.members.append(included_because_both_kinds_of_spans)
        db_session.flush()

        wanted = get_wanted_access(
            self.date(),
            group_ids_to_accessy_guids={
                group.group_id: TEST_GROUP_GUID,
            },
        )

        wanted_ids = {m.member_id for m in wanted.values()}

        self.assertIn(included_because_special_span.member_id, wanted_ids)
        self.assertIn(included_because_special_span.phone, wanted)
        assert included_because_special_span.phone is not None
        self.assertIn(ACCESSY_SPECIAL_LABACCESS_GROUP, wanted[included_because_special_span.phone].groups)

        self.assertIn(included_because_labaccess_span.member_id, wanted_ids)
        self.assertIn(included_because_labaccess_span.phone, wanted)
        assert included_because_labaccess_span.phone is not None
        self.assertIn(ACCESSY_LABACCESS_GROUP, wanted[included_because_labaccess_span.phone].groups)
        self.assertNotIn(TEST_GROUP_GUID, wanted[included_because_labaccess_span.phone].groups)

        self.assertIn(included_because_both_kinds_of_spans.member_id, wanted_ids)
        self.assertIn(included_because_both_kinds_of_spans.phone, wanted)

        assert included_because_both_kinds_of_spans.phone is not None
        self.assertIn(ACCESSY_LABACCESS_GROUP, wanted[included_because_both_kinds_of_spans.phone].groups)
        self.assertIn(ACCESSY_SPECIAL_LABACCESS_GROUP, wanted[included_because_both_kinds_of_spans.phone].groups)
        self.assertIn(TEST_GROUP_GUID, wanted[included_because_both_kinds_of_spans.phone].groups)

        self.assertNotIn(not_included_because_spans_outside_today.member_id, wanted_ids)
        self.assertNotIn(not_included_because_spans_outside_today.phone, wanted)

        self.assertIn(included_even_if_labaccess_agreement_not_signed.member_id, wanted_ids)
        self.assertIn(included_even_if_labaccess_agreement_not_signed.phone, wanted)

        self.assertNotIn(not_included_because_no_phone_number.member_id, wanted_ids)
        self.assertNotIn(not_included_because_no_phone_number.phone, wanted)

        self.assertNotIn(not_included_because_deleted.member_id, wanted_ids)
        self.assertNotIn(not_included_because_deleted.phone, wanted)
