from test_aid.systest_base import ApiTest


class Test(ApiTest):
    def test_memberbooth_can_get_member_by_number_even_if_member_does_not_have_a_key(self):
        member = self.db.create_member()

        self.api.get("/multiaccess/memberbooth/member", params=dict(member_number=member.member_number)).expect(
            200,
            data__keys=[],
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )

    def test_memberbooth_can_get_member_by_number(self):
        member = self.db.create_member()
        key = self.db.create_key()

        response = self.api.get("/multiaccess/memberbooth/member", params=dict(member_number=member.member_number))
        response.expect(
            200,
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )
        self.assertNotEqual([], response.data["keys"], "There exists keys")

    def test_memberbooth_can_get_member_by_tag(self):
        member = self.db.create_member()
        key = self.db.create_key()

        response = self.api.get("/multiaccess/memberbooth/tag", params=dict(tagid=key.tagid))
        response.expect(
            200,
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )
        self.assertNotEqual([], response.data["keys"], "There exists keys")

    def test_cannot_get_member_without_pin_set(self):
        member = self.db.create_member()  # Defaults without PIN

        self.api.get(
            "/multiaccess/memberbooth/pin-login",
            params=dict(member_number=member.member_number, pin_code=member.pin_code),
        ).is_not_ok()
        self.api.get(
            "/multiaccess/memberbooth/pin-login", params=dict(member_number=member.member_number, pin_code="")
        ).is_not_ok()

    def test_get_member_with_pin(self):
        member = self.db.create_member(pin_code=1234)

        response = self.api.get(
            "/multiaccess/memberbooth/pin-login",
            params=dict(member_number=member.member_number, pin_code=member.pin_code),
        )
        response.expect(200)

        response = self.api.get(
            "/multiaccess/memberbooth/pin-login", params=dict(member_number=member.member_number, pin_code="wrong pin")
        )
        response.expect(404)
