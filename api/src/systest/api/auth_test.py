import re

from test_aid.obj import DEFAULT_PASSWORD
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    def test_get_token_with_username_and_password(self):
        self.api.create_member(unhashed_password=DEFAULT_PASSWORD)
        username = self.api.member["email"]

        patten = re.compile(r"[A-Za-z0-9]{32}")

        # Using post parameters.
        token = (
            self.api.post(
                "/oauth/token",
                data=dict(grant_type="password", username=username, password=DEFAULT_PASSWORD),
                headers={},
            )
            .expect(code=200)
            .get("access_token")
        )

        self.assertTrue(patten.match(token))

        # Using url parameters.
        token = (
            self.api.post(
                "/oauth/token",
                params=dict(grant_type="password", username=username, password=DEFAULT_PASSWORD),
                headers={},
            )
            .expect(code=200)
            .get("access_token")
        )

        self.assertTrue(patten.match(token))

        # Using json content.
        token = (
            self.api.post(
                "/oauth/token",
                json=dict(grant_type="password", username=username, password=DEFAULT_PASSWORD),
                headers={},
            )
            .expect(code=200)
            .get("access_token")
        )

        self.assertTrue(patten.match(token))

    def test_get_token_with_bad_parameters(self):
        self.api.create_member(unhashed_password=DEFAULT_PASSWORD)
        username = self.api.member["email"]

        self.api.post("/oauth/token", data=dict(grant_type="not-correct")).expect(
            code=422, fields="grant_type", what="bad_value"
        )

        self.api.post(
            "/oauth/token", data=dict(grant_type="password", username=username + "wrong", password=DEFAULT_PASSWORD)
        ).expect(code=401)

        self.api.post(
            "/oauth/token", data=dict(grant_type="password", username=username, password=DEFAULT_PASSWORD + "wrong")
        ).expect(code=401)

    def test_delete_token_aka_logout(self):
        self.api.create_member(unhashed_password=DEFAULT_PASSWORD)
        username = self.api.member["email"]

        token = (
            self.api.post(
                "/oauth/token", data=dict(grant_type="password", username=username, password=DEFAULT_PASSWORD)
            )
            .expect(code=200)
            .get("access_token")
        )

        # Can't delete another persons token.
        self.api.delete(f"/oauth/token/{token}X", token=token).expect(code=404)

        # Delete own token works.
        self.api.delete(f"/oauth/token/{token}", token=token).expect(code=200)

        # Missing token in subsequent delete.
        self.api.delete(f"/oauth/token/{token}", token=token).expect(code=401)

    def test_list_access_tokens(self):
        self.api.create_member(unhashed_password=DEFAULT_PASSWORD)
        username = self.api.member["email"]

        token = (
            self.api.post(
                "/oauth/token", data=dict(grant_type="password", username=username, password=DEFAULT_PASSWORD)
            )
            .expect(code=200)
            .get("access_token")
        )

        tokens = self.api.get("/oauth/token", token=token).expect(code=200).data

        self.assertEqual([token], [t["access_token"] for t in tokens])
