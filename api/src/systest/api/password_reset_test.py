import re

from core.models import PasswordResetToken
from messages.models import Message
from service.db import db_session
from test_aid.obj import DEFAULT_PASSWORD
from test_aid.systest_base import ApiTest
from test_aid.test_util import random_str


class Test(ApiTest):

    def test_request_password_reset_with_correct_email_creates_message_with_token(self):
        self.db.create_member()
        username = self.db.member.email
        member_id = self.db.member.member_id

        print(member_id, username)
        
        self.api.post("/oauth/request_password_reset", data=dict(username=username), headers={}).expect(code=200)

        reset_token = db_session.query(PasswordResetToken).filter_by(member_id=member_id).one()
        
        message = db_session.query(Message).filter_by(member_id=member_id).one()
        
        self.assertIn(reset_token.token, message.body)

    def test_reset_password_returns_error_if_token_does_not_exist(self):
        e = self.api.post("/oauth/password_reset", data=dict(reset_token=random_str(), unhashed_password=random_str()))\
            .expect(code=200).get('data', 'error_message')
        
        assert e

    def test_reset_password_returns_error_if_token_is_expired(self):
        self.db.create_member()
        self.db.create_password_reset_token()
        
        e = self.api.post("/oauth/password_reset", data=dict(reset_token=random_str(), unhashed_password=random_str()))\
            .expect(code=200).get('data', 'error_message')
        
        assert e

    # def test_delete_token_aka_logout(self):
    #     self.api.create_member(unhashed_password=DEFAULT_PASSWORD)
    #     username = self.api.member['email']
    #
    #     token = self.api\
    #         .post("/oauth/token", data=dict(grant_type='password', username=username, password=DEFAULT_PASSWORD))\
    #         .expect(code=200).get('access_token')
    #
    #     # Can't delete another persons token.
    #     self.api.delete(f'/oauth/token/{token}X', token=token).expect(code=404)
    #
    #     # Delete own token works.
    #     self.api.delete(f'/oauth/token/{token}', token=token).expect(code=200)
    #
    #     # Missing token in subsequent delete.
    #     self.api.delete(f'/oauth/token/{token}', token=token).expect(code=401)
    #
    # def test_list_access_tokens(self):
    #     self.api.create_member(unhashed_password=DEFAULT_PASSWORD)
    #     username = self.api.member['email']
    #
    #     token = self.api\
    #         .post("/oauth/token", data=dict(grant_type='password', username=username, password=DEFAULT_PASSWORD))\
    #         .expect(code=200).get('access_token')
    #
    #     tokens = self.api.get('/oauth/token', token=token).expect(code=200).data
    #
    #     self.assertEqual([token], [t['access_token'] for t in tokens])
    #
    # def test_force_token_for_other_user_is_possible_for_service_user(self):
    #     self.api.create_member()
    #
    #     token = self.api\
    #         .post("/oauth/force_token", data=dict(user_id=self.api.member['member_id']))\
    #         .expect(code=200).get('access_token')
    #
    #     self.api.delete(f'/oauth/token/{token}', token=token).expect(code=200)
    #
    # def test_force_token_for_service_user_is_not_possible(self):
        self.api.post("/oauth/force_token", data=dict(user_id=-1)).expect(code=422)
