from datetime import datetime, timedelta
from random import randint
from unittest import skip
from unittest.mock import patch

from service.db import db_session
from test_aid.systest_base import ApiTest

from membership.models import PhoneNumberChangeRequest, Member, normalise_phone_number
from change_phone_request import change_phone_request, change_phone_validate

class Test(ApiTest):

    @patch('change_phone_request.send_validation_code')
    def test_request_and_validate(self, mock_send_validation_code):
        now = datetime.utcnow()
        new_phone = '+461234567'

        self.db.create_member()
        member = self.db.create_member()
        old_phone = member.phone
        
        change_phone_request(member.member_id, new_phone)

        db_item = db_session.query(PhoneNumberChangeRequest).filter(PhoneNumberChangeRequest.member_id == member.member_id).one()
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertFalse(db_item.completed)
        self.assertIsNotNone(db_item.validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        validation_code = db_item.validation_code
        mock_send_validation_code.assert_called()#(new_phone, validation_code)

        change_phone_validate(member.member_id, validation_code)

        db_item = db_session.query(PhoneNumberChangeRequest).filter(PhoneNumberChangeRequest.member_id == member.member_id).one()
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertTrue(db_item.completed)
        self.assertEqual(db_item.validation_code, validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        member_db = db_session.query(Member).filter(Member.member_id == member.member_id).one()
        self.assertEqual(member_db.phone, new_phone)
        self.assertNotEqual(member_db.phone, old_phone)

    #TODO tests with post

    #TODO test too many changes
    #TODO test incorrect validation code
    #TODO test not same phone namber as first in change
    #TODO various requests with different numbers one by one