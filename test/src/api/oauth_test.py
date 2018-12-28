import re

from aid.test.api import ApiTest
from aid.test.obj import DEFAULT_PASSWORD_HASH, DEFAULT_PASSWORD


class Test(ApiTest):

    def test_get_token_with_username_and_password(self):
        self.api.create_member(password=DEFAULT_PASSWORD_HASH)
        username = self.api.member['email']
        
        patten = re.compile(r'[A-Za-z0-9]{32}')
        
        # Using post parameters.
        token = self.api\
            .post("oauth/token", data=dict(grant_type='password', username=username, password=DEFAULT_PASSWORD))\
            .expect(code=200).get('access_token')
        self.assertTrue(patten.match(token))
        # TODO Ideally check db here, token and login.

        # Using url parameters.
        token = self.api\
            .post("oauth/token", params=dict(grant_type='password', username=username, password=DEFAULT_PASSWORD))\
            .expect(code=200).get('access_token')
        self.assertTrue(patten.match(token))

        # Using json content.
        token = self.api\
            .post("oauth/token", json=dict(grant_type='password', username=username, password=DEFAULT_PASSWORD))\
            .expect(code=200).get('access_token')
        self.assertTrue(patten.match(token))
        
    def test_get_token_with_bad_parameters(self):
        self.api.create_member(password=DEFAULT_PASSWORD_HASH)
        username = self.api.member['email']

        self.api.post("oauth/token", data=dict(grant_type='not-correct'))\
            .expect(code=422)  # TODO, fields='grant_type', what='bad_value')
        # TODO Ideally check db here, login and no token.

        self.api.post("oauth/token",
                      data=dict(grant_type='password', username=username + 'wrong', password=DEFAULT_PASSWORD))\
            .expect(code=401)  # TODO, fields='???', what='bad_value')

        self.api.post("oauth/token",
                      data=dict(grant_type='password', username=username, password=DEFAULT_PASSWORD + 'wrong'))\
            .expect(code=401)  # TODO, fields='???', what='bad_value')
