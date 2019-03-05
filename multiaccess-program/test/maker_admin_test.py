from copy import deepcopy
from datetime import datetime

from multi_access.maker_admin import MakerAdminClient
from test.base import BaseTest


valid_member = dict(
    member_id=1,
    member_number=1001,
    firstname="Kim",
    lastname="Larsson",
    start_date="2018-04-28",
    end_date="2018-05-28",
    keys=[dict(
        key_id=22,
        rfid_tag="123213433334",
    )],
)


class ParseTest(BaseTest):

    def test_parse_valid_member(self):
        m, = MakerAdminClient.response_data_to_members([valid_member])
        self.assertEqual(1001, m.member_number)
        self.assertEqual("Kim", m.firstname)
        self.assertEqual("Larsson", m.lastname)
        self.assertEqual("123213433334", m.rfid_tag)
        self.assertEqual(datetime(2018, 5, 28, 23, 59, 59), m.end_timestamp)

    def test_parse_valid_with_no_end_timestamp(self):
        obj = deepcopy(valid_member)
        obj['end_date'] = None
        m, = MakerAdminClient.response_data_to_members([obj])
        self.assertEqual(1001, m.member_number)
        self.assertEqual("Kim", m.firstname)
        self.assertEqual("Larsson", m.lastname)
        self.assertEqual("123213433334", m.rfid_tag)
        self.assertEqual(None, m.end_timestamp)

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
        test_bad(end_date="XYZ")

        def test_bad_key(**kwargs):
            obj = deepcopy(valid_member)
            obj['keys'][0].update(kwargs)
            with self.assertRaises(ValueError):
                MakerAdminClient.response_data_to_members([obj])

        test_bad_key(key_id=False)
        test_bad_key(rfid_tag=244)

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
                end_date="2018-05-28",
                keys=[
                    dict(
                        key_id=4,
                        rfid_tag="4",
                    ),
                    dict(
                        key_id=2,
                        rfid_tag="2",
                    ),
                    dict(
                        key_id=1,
                        rfid_tag="1",
                    ),
                    dict(
                        key_id=3,
                        rfid_tag="3",
                    ),
                ],
            )
        ])
        self.assertEqual("4", m.rfid_tag)
