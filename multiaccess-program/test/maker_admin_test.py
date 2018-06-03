from copy import copy, deepcopy
from datetime import datetime

from multi_access.maker_admin import MakerAdminClient
from multi_access.util import dt_parse
from test.base import BaseTest


valid_member = dict(
    member_id=1,
    member_number=1001,
    firstname="Kim",
    lastname="Larsson",
    keys=[dict(
        key_id=22,
        rfid_tag="123213433334",
        blocked=False,
        start_timestamp="2018-04-28T10:10:10+02:00",
        end_timestamp="2018-05-28T10:10:10+02:00",
    )],
)


class ParseTest(BaseTest):

    def test_parse_valid_member(self):
        m, = MakerAdminClient.response_data_to_members([valid_member])
        self.assertEqual(1001, m.member_number)
        self.assertEqual("Kim", m.firstname)
        self.assertEqual("Larsson", m.lastname)
        self.assertEqual("123213433334", m.rfid_tag)
        self.assertEqual(datetime(2018, 5, 28, 10, 10, 10), m.end_timestamp)

    def test_parse_bad_member(self):
        def test_bad(**kwargs):
            obj = deepcopy(valid_member)
            obj.update(kwargs)
            with self.assertRaises(ValueError):
                MakerAdminClient.response_data_to_members([obj])
            
        test_bad(member_id="bad id")
        test_bad(member_number="not a number")
        test_bad(firstname=123)
        test_bad(lastname=3334)

        def test_bad_key(**kwargs):
            obj = deepcopy(valid_member)
            obj['keys'][0].update(kwargs)
            with self.assertRaises(ValueError):
                MakerAdminClient.response_data_to_members([obj])

        test_bad_key(key_id=False)
        test_bad_key(rfid_tag=244)
        test_bad_key(blocked="status")
        test_bad_key(end_timestamp="XYZ")

    def test_blocked_key_is_filtered(self):
        obj = deepcopy(valid_member)
        obj['keys'][0]['blocked'] = True
        self.assertEqual([], MakerAdminClient.response_data_to_members([obj]))

    def test_no_end_timestamp_is_filtered(self):
        obj = deepcopy(valid_member)
        obj['keys'][0]['end_timestamp'] = None
        self.assertEqual([], MakerAdminClient.response_data_to_members([obj]))

    def test_no_keys_is_filtered(self):
        obj = deepcopy(valid_member)
        obj['keys'] = []
        self.assertEqual([], MakerAdminClient.response_data_to_members([obj]))

    def test_unblocked_key_with_latest_end_timestamp_is_picked(self):
        m, = MakerAdminClient.response_data_to_members([
            dict(
                member_id=1,
                member_number=1001,
                firstname="Kim",
                lastname="Larsson",
                keys=[
                    dict(
                        key_id=1,
                        rfid_tag="1",
                        blocked=False,
                        start_timestamp=None,
                        end_timestamp="2018-05-28T10:00:00+02:00",
                    ),
                    dict(
                        key_id=2,
                        rfid_tag="2",
                        blocked=True,
                        start_timestamp=None,
                        end_timestamp="2018-05-28T18:00:00+02:00",
                    ),
                    dict(
                        key_id=3,
                        rfid_tag="3",
                        blocked=False,
                        start_timestamp=None,
                        end_timestamp="2018-05-28T12:00:00+02:00",
                    ),
                    dict(
                        key_id=4,
                        rfid_tag="4",
                        blocked=False,
                        start_timestamp=None,
                        end_timestamp="2018-05-28T13:00:00+04:00",
                    )
                ],
            )
        ])
        self.assertEqual("3", m.rfid_tag)
