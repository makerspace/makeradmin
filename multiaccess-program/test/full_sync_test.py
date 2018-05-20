from unittest.mock import MagicMock, patch

from multi_access.maker_admin import MakerAdminClient
from multi_access.models import User
from multi_access.tui import Tui
from sync_main import sync
from test.db_base import DbBaseTest
from test.factory import UserFactory, MakerAdminMemberFactory, CustomerFactory
from multi_access.util import dt_cet_local


class Test(DbBaseTest):
    
    def setUp(self):
        super().setUp()
        self.client = MakerAdminClient(base_url="https://makeradmin.se")
        self.ui = Tui()

    @patch('builtins.input', lambda m: '')
    def test_super_simple_sync_updates_one_end_timestamp(self):
        c = CustomerFactory()

        old_stop = dt_cet_local(self.datetime(days=30))
        u = UserFactory(stop_timestamp=old_stop, name="1001", customer=c)
        
        new_stop = self.datetime(days=50)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=new_stop)
        
        self.client.fetch_members = MagicMock(return_value=[m])
        
        sync(session=self.session, client=self.client, ui=self.ui, customer_id=c.id)
        
        u = self.session.query(User).get(u.id)
        self.assertEqual(dt_cet_local(new_stop), u.stop_timestamp)
