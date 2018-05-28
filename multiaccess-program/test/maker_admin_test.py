from copy import copy
from unittest.mock import MagicMock

from multi_access.maker_admin import MakerAdminClient
from multi_access.tui import Tui
from test.base import BaseTest


valid_member = dict(
    member_id=1,
    member_number=1001,
    firstname="Kim",
    lastname="Larsson",
    key_id=22,
    rfid_tag="1232134333340",
    blocked=False,
    end_timestamp="2018-05-28T10:10:10.000000Z",
)


class ParseTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.client = MakerAdminClient(base_url="https://makeradmin.se")
        self.tui = Tui()
    
    def test_parse_valid_members(self):
        self.client.get_and_login_if_needed = MagicMock(return_value={"data": [valid_member]})
        self.client.fetch_members(self.tui)

    def test_parse_bad_member(self):
        def test_bad(**kwargs):
            obj = copy(valid_member)
            obj.update(kwargs)
            self.client.get_and_login_if_needed = MagicMock(return_value={"data": [obj]})
            with self.assertRaises(ValueError):
                self.client.fetch_members(self.tui)
            
        test_bad(member_id="bad id")
        test_bad(member_number="not a number")
        test_bad(firstname=123)
        test_bad(lastname=3334)
        test_bad(key_id=False)
        test_bad(rfid_tag=244)
        test_bad(blocked="status")
        test_bad(end_timestamp="2018-05-03 10:13:41.333000Z")
        test_bad(end_timestamp="2018-05-03T10:13:41.3330")
        test_bad(end_timestamp="20180503T10:13:41.333000Z")
        test_bad(end_timestamp="2018-05-03T10:13:41.333000+0200")
        
        
