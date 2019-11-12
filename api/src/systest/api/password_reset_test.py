from core.models import PasswordResetToken
from membership.member_auth import verify_password
from membership.models import Member
from messages.models import Message
from service.db import db_session
from test_aid.systest_base import ApiTest
from test_aid.test_util import random_str


class Test(ApiTest):

    def test_request_password_reset_with_correct_email_creates_message_with_token(self):
        member = self.db.create_member()

        self.api.post("/oauth/request_password_reset", data=dict(username=member.email), headers={}).expect(code=200)

        reset_token = db_session.query(PasswordResetToken).filter_by(member_id=member.member_id).one()
        message = db_session.query(Message).filter_by(member_id=member.member_id).one()
        self.assertIn(reset_token.token, message.body)

    def test_reset_password_returns_error_if_token_does_not_exist(self):
        e = self.api.post("/oauth/password_reset", data=dict(reset_token=random_str(), unhashed_password=random_str()))\
            .expect(code=200).get('data__error_message')
        
        self.assertIn("could not find", e.lower())

    def test_reset_password_returns_error_if_token_is_expired(self):
        self.db.create_member()
        reset_token = self.db.create_password_reset_token(created_at=self.datetime(minutes=-11))
        
        e = self.api.post("/oauth/password_reset",
                          data=dict(reset_token=reset_token.token, unhashed_password=random_str()))\
            .expect(code=200).get('data__error_message')
        
        self.assertIn("expired", e.lower())

    def test_reset_password_returns_error_if_pwd_is_to_short(self):
        self.db.create_member()
        reset_token = self.db.create_password_reset_token()
        
        e = self.api.post("/oauth/password_reset",
                          data=dict(reset_token=reset_token.token, unhashed_password=random_str(3)))\
            .expect(code=200).get('data__error_message')
        
        self.assertIn("at least", e.lower())

    def test_reset_password_works_for_nice_password(self):
        member_id = self.db.create_member().member_id
        reset_token = self.db.create_password_reset_token()
        
        unhashed_password = random_str()
        
        e = self.api.post("/oauth/password_reset",
                          data=dict(reset_token=reset_token.token, unhashed_password=unhashed_password))\
            .expect(code=200).get('data__error_message')
        
        self.assertIsNone(e)
        
        member = db_session.query(Member).get(member_id)
        
        self.assertTrue(verify_password(unhashed_password, member.password))
