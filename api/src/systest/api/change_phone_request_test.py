from datetime import datetime
from random import randint
from unittest import skip

from service.db import db_session
from test_aid.systest_base import ApiTest

from membership.models import PhoneNumberChangeRequest
from change_phone_request import change_phone_request, change_phone_validate

class Test(ApiTest):

    #TODO mock sms sending

    def test_request_and_validate(self):
        phone = 1 #TODO
        member = self.db.create_member()
        
        change_phone_request(member.member_id, phone)

        change_phone_validate(member.member_id, phone, validation_code)

    #TODO tests with post
