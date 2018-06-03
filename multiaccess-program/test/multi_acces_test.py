from random import shuffle

from multi_access.models import User, AuthorityInUser
from multi_access.multi_access import DbMember, diff_member_update, UpdateMember, diff_member_missing, \
    AddMember, update_diffs, diff_blocked, BlockMember
from multi_access.tui import Tui
from test.db_base import DbBaseTest
from test.factory import UserFactory, MakerAdminMemberFactory, CustomerFactory, AuthorityFactory


class TestUpdateDiff(DbBaseTest):
    
    def setUp(self):
        super().setUp()
        self.tui = Tui()
    
    def test_simple_no_diff(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(), name="1001", card="3"))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), rfid_tag="3")
        
        self.assertEqual([], diff_member_update([d], [m]))

    def test_multiple_unsorted_no_diff(self):
        ds = [DbMember(UserFactory(stop_timestamp=self.datetime(days=i), name=str(i), card=str(i)))
              for i in range(1001, 1010)]
        shuffle(ds)
        ms = [MakerAdminMemberFactory(member_number=i, end_timestamp=self.datetime(days=i), rfid_tag=str(i))
              for i in range(1001, 1010)]
        shuffle(ms)
        
        self.assertEqual([], diff_member_update(ds, ms))
        
    def test_simple_diff_on_timestamp(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime())
        
        self.assertEqual([UpdateMember(d, m)], diff_member_update([d], [m]))

    def test_simple_diff_on_blocked(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(), name="1001", blocked=True))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime())
        
        self.assertEqual([UpdateMember(d, m)], diff_member_update([d], [m]))

    def test_simple_diff_tag(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(), name="1001", card="1"))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), rfid_tag="2")
        
        self.assertEqual([UpdateMember(d, m)], diff_member_update([d], [m]))

    def test_milisecond_diff_creates_no_diff(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(milliseconds=1), name="1001", blocked=False, card="1"))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), rfid_tag="1")
        
        self.assertEqual([], diff_member_update([d], [m]))

    def test_two_different_members_creates_no__diff(self):
        d = DbMember(UserFactory(stop_timestamp=self.datetime(), name="1002"))
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime())
        
        self.assertEqual([], diff_member_update([d], [m]))

    def test_multiple_diffs_and_multiple_non_diffs_works(self):
        d1 = DbMember(UserFactory(stop_timestamp=self.datetime(days=1), name="1001", card="1", blocked=False))
        d2 = DbMember(UserFactory(stop_timestamp=self.datetime(days=2), name="1002", card="2", blocked=False))
        d3 = DbMember(UserFactory(stop_timestamp=self.datetime(days=3), name="1003", card="3", blocked=False))
        d4 = DbMember(UserFactory(stop_timestamp=self.datetime(days=4), name="1004", card="4", blocked=True))
        d5 = DbMember(UserFactory(stop_timestamp=self.datetime(days=5), name="1005", card="X", blocked=False))
        dx = DbMember(UserFactory(stop_timestamp=self.datetime(days=0), name="2001", card="1", blocked=False))
        m1 = MakerAdminMemberFactory(member_number=1001, rfid_tag="1", end_timestamp=self.datetime(days=1))
        m2 = MakerAdminMemberFactory(member_number=1002, rfid_tag="2", end_timestamp=self.datetime(days=8))
        m3 = MakerAdminMemberFactory(member_number=1003, rfid_tag="3", end_timestamp=self.datetime(days=3))
        m4 = MakerAdminMemberFactory(member_number=1004, rfid_tag="4", end_timestamp=self.datetime(days=4))
        m5 = MakerAdminMemberFactory(member_number=1005, rfid_tag="5", end_timestamp=self.datetime(days=5))
        mx = MakerAdminMemberFactory(member_number=3001, rfid_tag="1", end_timestamp=self.datetime(days=1))
        
        diffs = diff_member_update([d1, d2, d3, d4, d5, dx], [mx, m1, m2, m3, m4, m5])
        self.assertIn(UpdateMember(d2, m2), diffs)
        self.assertIn(UpdateMember(d4, m4), diffs)
        self.assertIn(UpdateMember(d5, m5), diffs)
        self.assertEqual(3, len(diffs))

    def test_update_diff_changes_timestamp_when_called(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False)
        d = DbMember(u)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=2))
        etd = UpdateMember(d, m)
        
        etd.update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=2), u.stop_timestamp)
        self.assertFalse(u.blocked)

    def test_update_diff_changes_tag_when_called(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False, card="1")
        d = DbMember(u)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=1), rfid_tag="2")
        etd = UpdateMember(d, m)
        
        etd.update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=1), u.stop_timestamp)
        self.assertEqual("2", u.card)
        self.assertFalse(u.blocked)

    def test_update_diff_changes_blocked_when_called(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=True, card="1")
        d = DbMember(u)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=1), rfid_tag="1")
        etd = UpdateMember(d, m)
        
        etd.update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=1), u.stop_timestamp)
        self.assertEqual("1", u.card)
        self.assertFalse(u.blocked)

    def test_update_diff_changes_all_three_values_when_both_diffs(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=True, card="1")
        d = DbMember(u)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=2), rfid_tag="2")
        etd = UpdateMember(d, m)
        
        etd.update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=2), u.stop_timestamp)
        self.assertEqual("2", u.card)
        self.assertFalse(u.blocked)
        
       
class TestMemberAddDiff(DbBaseTest):
    
    def setUp(self):
        super().setUp()
        self.tui = Tui()
    
    def test_simple_no_diff(self):
        d = DbMember(UserFactory(name="1001"))
        m = MakerAdminMemberFactory(member_number=1001)
        
        self.assertEqual([], diff_member_missing([d], [m]))

    def test_multiple_unsorted_no_diff(self):
        ds = [DbMember(UserFactory(name=str(i))) for i in range(1001, 1010)]
        shuffle(ds)
        ms = [MakerAdminMemberFactory(member_number=i) for i in range(1001, 1010)]
        shuffle(ms)
        
        self.assertEqual([], diff_member_missing(ds, ms))
        
    def test_simple_diff_add_one_user(self):
        m = MakerAdminMemberFactory(member_number=1001)
        
        self.assertEqual([AddMember(m)], diff_member_missing([], [m]))

    def test_excessive_db_user_creates_no_diff(self):
        d = DbMember(UserFactory(name="1001"))
        
        self.assertEqual([], diff_member_missing([d], []))

    def test_multiple_diffs_and_multiple_non_diffs_works(self):
        ds = [DbMember(UserFactory(name=n)) for n in ["1001", "1002", "1003"]]
        ms = [MakerAdminMemberFactory(member_number=n) for n in [1001, 1003, 1004, 1005]]
        
        diffs = [d.m.member_number for d in diff_member_missing(ds, ms)]
        self.assertCountEqual([1004, 1005], diffs)
        
    def test_update_diff_adds_member_and_auth(self):
        c = CustomerFactory()
        a = AuthorityFactory()
        m = MakerAdminMemberFactory(member_number=1001, rfid_tag='4444', end_timestamp=self.datetime())
        
        AddMember(m).update(self.session, self.tui, customer_id=c.id, authority_id=a.id)
        
        users = self.session.query(User).all()
        print(users)
        self.assertEqual(1, len(users))
        
        u = users[0]
        self.assertEqual("1001", u.name)
        self.assertEqual(self.datetime(), u.stop_timestamp)
        self.assertEqual(None, u.blocked)
        self.assertEqual("4444", u.card)
        self.assertEqual(c.id, u.customer_id)
        
        auths = self.session.query(AuthorityInUser).filter_by(user_id=u.id).all()
        self.assertEqual(1, len(auths))
        
        auth = auths[0]
        self.assertEqual(a.id, auth.authority_id)

    def test_update_diffs_fails_on_sanity_check_if_wrong_customer_name(self):
        c = CustomerFactory(name="makerspace stockholm")
        a = AuthorityFactory()
        m = MakerAdminMemberFactory()
        
        with self.assertRaises(Exception):
            update_diffs(self.session, self.tui, [AddMember(m)], customer_id=c.id, authority_id=a.id)

    def test_update_diffs_fails_on_sanity_check_if_wrong_authority_name(self):
        c = CustomerFactory()
        a = AuthorityFactory(name="makerspace stockholm")
        m = MakerAdminMemberFactory()
        
        with self.assertRaises(Exception):
            update_diffs(self.session, self.tui, [AddMember(m)], customer_id=c.id, authority_id=a.id)


class TestMemberBlockDiff(DbBaseTest):
    
    def setUp(self):
        super().setUp()
        self.tui = Tui()
    
    def test_simple_no_diff(self):
        d = DbMember(UserFactory(name="1001"))
        m = MakerAdminMemberFactory(member_number=1001)
        
        self.assertEqual([], diff_blocked([d], [m]))

    def test_multiple_unsorted_no_diff(self):
        ds = [DbMember(UserFactory(name=str(i))) for i in range(1001, 1010)]
        shuffle(ds)
        ms = [MakerAdminMemberFactory(member_number=i) for i in range(1001, 1010)]
        shuffle(ms)
        
        self.assertEqual([], diff_blocked(ds, ms))
        
    def test_simple_diff_block_one_user(self):
        d = DbMember(UserFactory(name="1001"))
        
        self.assertEqual([BlockMember(d)], diff_blocked([d], []))

    def test_no_block_diff_if_already_blocked(self):
        d = DbMember(UserFactory(name="1001", blocked=True))
        
        self.assertEqual([], diff_blocked([d], []))

    def test_excessive_ma_user_creates_no_diff(self):
        m = MakerAdminMemberFactory(member_number=1001)
        
        self.assertEqual([], diff_blocked([], [m]))

    def test_multiple_diffs_and_multiple_non_diffs_works(self):
        ds = [DbMember(UserFactory(name=n)) for n in ["1001", "1002", "1003"]]
        ms = [MakerAdminMemberFactory(member_number=n) for n in [1001, 1003, 1004, 1005]]
        
        diffs = [d.db_member.member_number for d in diff_blocked(ds, ms)]
        self.assertCountEqual([1002], diffs)
        
    def test_update_diff_blocks_member(self):
        u = UserFactory(stop_timestamp=self.datetime(days=1), name="1001", blocked=False, card="1")
        d = DbMember(u)
        BlockMember(d).update(self.session, self.tui)
        
        self.session.refresh(u)
        
        self.assertEqual(self.datetime(days=1), u.stop_timestamp)
        self.assertEqual("1", u.card)
        self.assertTrue(u.blocked)
