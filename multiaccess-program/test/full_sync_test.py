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
    def test_sync_updates_one_end_timestamp(self):
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
