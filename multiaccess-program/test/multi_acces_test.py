from random import shuffle

from multi_access.multi_access import DbMember, create_end_timestamp_diff, EndTimestampDiff
from multi_access.tui import Tui
from test.db_base import DbBaseTest
from test.factory import UserFactory, MakerAdminMemberFactory


class Test(DbBaseTest):
    
    def setUp(self):
        super().setUp()
        self.tui = Tui()
    
    def test_simple_no_diff(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(), name="1001", blocked=False))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), blocked=False)
        
        self.assertEqual([], create_end_timestamp_diff([d], [m]))

    def test_multiple_unsorted_no_diff(self):
        ds = [DbMember(UserFactory(stop_timestamp=self.datetime(days=i), name=str(i), blocked=bool(i % 2)))
              for i in range(1001, 1010)]
        shuffle(ds)
        ms = [MakerAdminMemberFactory(member_number=i, end_timestamp=self.datetime(days=i), blocked=bool(i % 2))
              for i in range(1001, 1010)]
        shuffle(ms)
        
        self.assertEqual([], create_end_timestamp_diff(ds, ms))
        
    def test_simple_diff_on_timestamp(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), blocked=False)
        
        self.assertEqual([EndTimestampDiff(d, m)], create_end_timestamp_diff([d], [m]))

    def test_simple_diff_on_blocked(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(), name="1001", blocked=False))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), blocked=True)
        
        self.assertEqual([EndTimestampDiff(d, m)], create_end_timestamp_diff([d], [m]))

    def test_two_differente_members_creates_no_end_timestamp_diff(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(), name="1002", blocked=False))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), blocked=True)
        
        self.assertEqual([], create_end_timestamp_diff([d], [m]))

    def test_multiple_diffs_and_multiple_non_diffs_works(self):
        d1 = DbMember(UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False))
        d2 = DbMember(UserFactory(stop_timestamp=self.datetime(days=2), name="1002", blocked=True))
        d3 = DbMember(UserFactory(stop_timestamp=self.datetime(days=3), name="1003", blocked=False))
        d4 = DbMember(UserFactory(stop_timestamp=self.datetime(days=4), name="1004", blocked=True))
        d5 = DbMember(UserFactory(stop_timestamp=self.datetime(days=5), name="1005", blocked=False))
        m1 = MakerAdminMemberFactory(member_number=1401, end_timestamp=self.datetime(days=1), blocked=False)
        m2 = MakerAdminMemberFactory(member_number=1002, end_timestamp=self.datetime(days=8), blocked=True)
        m3 = MakerAdminMemberFactory(member_number=1003, end_timestamp=self.datetime(days=3), blocked=False)
        m4 = MakerAdminMemberFactory(member_number=1004, end_timestamp=self.datetime(days=4), blocked=False)
        m5 = MakerAdminMemberFactory(member_number=1405, end_timestamp=self.datetime(days=5), blocked=False)
        
        diffs = create_end_timestamp_diff([d1, d2, d3, d4, d5], [m1, m2, m3, m4, m5])
        self.assertIn(EndTimestampDiff(d2, m2), diffs)
        self.assertIn(EndTimestampDiff(d4, m4), diffs)
        self.assertEqual(2, len(diffs))

    def test_update_diff_changes_timestamp_when_changed(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False)
        d = DbMember(u)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=2), blocked=False)
        etd = EndTimestampDiff(d, m)
        
        etd.update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=2), u.stop_timestamp)
        self.assertFalse(u.blocked)

    def test_update_diff_changes_blocked_when_changed(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False)
        d = DbMember(u)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=1), blocked=True)
        etd = EndTimestampDiff(d, m)
        
        etd.update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=1), u.stop_timestamp)
        self.assertTrue(u.blocked)

    def test_update_diff_changes_both_values_when_both_diffs(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False)
        d = DbMember(u)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=2), blocked=True)
        etd = EndTimestampDiff(d, m)
        
        etd.update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=2), u.stop_timestamp)
        self.assertTrue(u.blocked)
        
        