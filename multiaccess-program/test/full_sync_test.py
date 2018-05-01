from unittest import mock

from multi_access.models import User
from multi_access.tui import Tui
from sync_main import sync
from test.db_base import DbBaseTest
from test.factory import UserFactory, MakerAdminMemberFactory
from multi_access.util import dt_cet_local


class Test(DbBaseTest):

    def test_meta(self):
        m = MakerAdminMemberFactory()
        print(m)
    
    def test_super_simple_sync_updates_one_end_timestamp(self):

        old_stop = dt_cet_local(self.datetime(days=30))
        UserFactory(stop_timestamp=old_stop, name="1001")
    
        new_stop = self.datetime(days=50)
        m = MakerAdminMemberFactory(member_number=1001, end_timestamp=self.datetime(days=30))
        
        with mock.patch('multi_access.maker_admin.fetch_maker_admin_members', side_effect=lambda: [m]):
            sync(Tui(), self.session, "http://fake/url")
            
        u = self.session.query(User).filter(name="1001").one()
        self.assertEqual(dt_cet_local(new_stop), u.stop_timestamp)

