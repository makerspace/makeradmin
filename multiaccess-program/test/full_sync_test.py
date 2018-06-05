from unittest.mock import MagicMock, patch

from multi_access.maker_admin import MakerAdminClient
from multi_access.models import User, AuthorityInUser
from multi_access.tui import Tui
from sync_main import sync
from test.db_base import DbBaseTest
from test.factory import UserFactory, MakerAdminMemberFactory, CustomerFactory, AuthorityFactory


class Test(DbBaseTest):
    
    def setUp(self):
        super().setUp()
        self.client = MakerAdminClient(base_url="https://makeradmin.se")
        self.ui = Tui()

    @patch('builtins.input', lambda m: 'go')
    def test_sync_updates_end_timestamp(self):
        c = CustomerFactory()
        a = AuthorityFactory()

        old_stop = self.datetime(days=30)
        u = UserFactory(stop_timestamp=old_stop, name="1001", customer=c)
        
        new_stop = self.datetime(days=50)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=new_stop)
        
        self.client.fetch_members = MagicMock(return_value=[m])
        
        sync(session=self.session, client=self.client, ui=self.ui, customer_id=c.id, authority_id=a.id)
        
        u = self.session.query(User).get(u.id)
        self.assertEqual(new_stop, u.stop_timestamp)

    @patch('builtins.input', lambda m: 'go')
    def test_sync_updates_rfid_tag(self):
        c = CustomerFactory()
        a = AuthorityFactory()

        u = UserFactory(stop_timestamp=self.datetime(), name="1001", customer=c, card="1")
        
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), rfid_tag="2")
        
        self.client.fetch_members = MagicMock(return_value=[m])
        
        sync(session=self.session, client=self.client, ui=self.ui, customer_id=c.id, authority_id=a.id)
        
        u = self.session.query(User).get(u.id)
        self.assertEqual("2", u.card)

    @patch('builtins.input', lambda m: '')
    def test_no_update_is_made_when_user_breaks(self):
        c = CustomerFactory()
        a = AuthorityFactory()

        old_stop = self.datetime(days=30)
        u = UserFactory(stop_timestamp=old_stop, name="1001", customer=c)
        
        new_stop = self.datetime(days=50)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=new_stop)
        
        self.client.fetch_members = MagicMock(return_value=[m])
        
        with self.assertRaises(SystemExit):
            sync(session=self.session, client=self.client, ui=self.ui, customer_id=c.id, authority_id=a.id)
        
        u = self.session.query(User).get(u.id)
        self.assertEqual(old_stop, u.stop_timestamp)

    @patch('builtins.input', lambda m: 'go')
    def test_add_one_member(self):
        c = CustomerFactory()
        a = AuthorityFactory()

        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(), rfid_tag="123")
        
        self.client.fetch_members = MagicMock(return_value=[m])
        
        sync(session=self.session, client=self.client, ui=self.ui, customer_id=c.id, authority_id=a.id)
        
        users = self.session.query(User).all()
        self.assertEqual(1, len(users))
        
        u = users[0]
        self.assertEqual("1001", u.name)
        self.assertEqual(self.datetime(), u.stop_timestamp)
        self.assertEqual(False, bool(u.blocked))
        self.assertEqual("123", u.card)
        self.assertEqual(c.id, u.customer_id)
        
        auths = self.session.query(AuthorityInUser).filter_by(user_id=u.id).all()
        self.assertEqual(1, len(auths))
        
        auth = auths[0]
        self.assertEqual(a.id, auth.authority_id)

    @patch('builtins.input', lambda m: 'go')
    def test_block_one_member(self):
        c = CustomerFactory()
        a = AuthorityFactory()
        
        u = UserFactory(stop_timestamp=self.datetime(), name="1001", customer=c)
        
        self.client.fetch_members = MagicMock(return_value=[])
        
        sync(session=self.session, client=self.client, ui=self.ui, customer_id=c.id, authority_id=a.id)
        
        u = self.session.query(User).get(u.id)
        self.assertTrue(u.blocked)

    @patch('builtins.input', lambda m: 'go')
    def test_sync_with_multiple_changes_non_changes_and_other_customers(self):
        other_customer = CustomerFactory()
        other_authority = AuthorityFactory()
        
        customer = CustomerFactory()
        authority = AuthorityFactory()
        
        # Users to update.
        u1 = UserFactory(stop_timestamp=self.datetime(), name="1001", card="1", blocked=True, customer=customer)
        u2 = UserFactory(stop_timestamp=self.datetime(), name="1002", card="2", blocked=None, customer=customer)
        
        # Users to block.
        u3 = UserFactory(stop_timestamp=self.datetime(), name="1003", card="3", blocked=None, customer=customer)
        u4 = UserFactory(stop_timestamp=self.datetime(), name="1004", card="4", blocked=None, customer=customer)
        
        # Other users not to be touched.
        u5 = UserFactory(stop_timestamp=self.datetime(), name="1005", card="5", blocked=None, customer=other_customer)
        u6 = UserFactory(stop_timestamp=self.datetime(), name="1006", card="6", blocked=None, customer=other_customer)
        u7 = UserFactory(stop_timestamp=self.datetime(), name="1007", card="7", blocked=None, customer=other_customer)
        u8 = UserFactory(stop_timestamp=self.datetime(), name="1008", card="8", blocked=None, customer=other_customer)
        
        self.client.fetch_members = MagicMock(return_value=[
            # Updates.
            MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=1), rfid_tag="1"),
            MakerAdminMemberFactory(member_number=1002, end_timestamp=self.datetime(), rfid_tag="22"),
            # Creates.
            MakerAdminMemberFactory(member_number=1007, end_timestamp=self.datetime(days=7), rfid_tag="77"),
            MakerAdminMemberFactory(member_number=1008, end_timestamp=self.datetime(days=8), rfid_tag="88"),
        ])
        
        sync(session=self.session, client=self.client, ui=self.ui, customer_id=customer.id, authority_id=authority.id)
        
        self.session.refresh(u5)
        self.assertEqual("5", u5.card)
        self.assertEqual(self.datetime(), u5.stop_timestamp)
        
        self.session.refresh(u6)
        self.assertEqual("6", u6.card)
        self.assertEqual(self.datetime(), u6.stop_timestamp)

        self.session.refresh(u7)
        self.assertEqual("7", u7.card)
        self.assertEqual(self.datetime(), u7.stop_timestamp)

        self.session.refresh(u8)
        self.assertEqual("8", u8.card)
        self.assertEqual(self.datetime(), u8.stop_timestamp)

        [u1, u2, u3, u4, u7, u8] = self.session.query(User).filter_by(customer=customer).order_by(User.name)
        
        self.assertEqual("1001", u1.name)
        self.assertEqual("1", u1.card)
        self.assertEqual(False, u1.blocked)
        self.assertEqual(self.datetime(days=1), u1.stop_timestamp)
        
        self.assertEqual("1002", u2.name)
        self.assertEqual("22", u2.card)
        self.assertEqual(False, u2.blocked)
        self.assertEqual(self.datetime(), u2.stop_timestamp)
        
        self.assertEqual("1003", u3.name)
        self.assertEqual("3", u3.card)
        self.assertEqual(True, u3.blocked)
        self.assertEqual(self.datetime(), u3.stop_timestamp)
        
        self.assertEqual("1004", u4.name)
        self.assertEqual("4", u4.card)
        self.assertEqual(True, u4.blocked)
        self.assertEqual(self.datetime(), u4.stop_timestamp)
        
        self.assertEqual("1007", u7.name)
        self.assertEqual("77", u7.card)
        self.assertEqual(None, u7.blocked)
        self.assertEqual(self.datetime(days=7), u7.stop_timestamp)
        
        self.assertEqual("1008", u8.name)
        self.assertEqual("88", u8.card)
        self.assertEqual(None, u8.blocked)
        self.assertEqual(self.datetime(days=8), u8.stop_timestamp)
        
