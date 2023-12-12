from test_aid.systest_base import ApiTest
from test_aid.test_util import random_str


class Test(ApiTest):
    # Tests for members that are not covered by entity tests.

    def test_create_member_with_existing_email_fails(self):
        member = self.obj.create_member()
        self.post("/membership/member", json=member).expect(code=201).get("data__member_number")
        self.post("/membership/member", json=member).expect(code=422, status="error", what="not_unique", fields="email")

    def test_create_almost_duplicate_member_ok(self):
        member = self.obj.create_member()
        self.post("/membership/member", json=member).expect(code=201).get("data__member_number")
        member["email"] = member["email"] + "-not-duplicate"
        self.post("/membership/member", json=member).expect(code=201)

    def test_create_member_gives_new_member_numbers_and_ids(self):
        member1 = self.obj.create_member()
        member2 = self.obj.create_member()

        id1, number1 = (
            self.post("/membership/member", json=member1).expect(code=201).get("data__member_id", "data__member_number")
        )

        id2, number2 = (
            self.post("/membership/member", json=member2).expect(code=201).get("data__member_id", "data__member_number")
        )

        self.assertNotEqual(id1, id2)
        self.assertNotEqual(number1, number2)

    def test_create_password_using_unhashed_password(self):
        pwd = random_str(16)
        member = self.api.create_member(password=None, unhashed_password=pwd)
        self.post("/oauth/token", {"grant_type": "password", "username": member["email"], "password": pwd}).expect(
            code=200
        )

    def test_update_password_using_unhashed_password(self):
        pwd = random_str(16)
        member = self.db.create_member()
        self.put(f"/membership/member/{member.member_id}", dict(unhashed_password=pwd)).expect(200)
        self.post("/oauth/token", {"grant_type": "password", "username": member.email, "password": pwd}).expect(
            code=200
        )
