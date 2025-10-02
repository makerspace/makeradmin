from test_aid.api import ApiResponse  # Assuming this is the type returned by self.api.get()
from test_aid.db import (  # Assuming these are the types returned by self.db.create_member() and self.db.create_key()
    Key,
    Member,
)
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    def test_memberbooth_can_get_member_by_number_even_if_member_does_not_have_a_key(self) -> None:
        assert self.api is not None
        member: Member = self.db.create_member()

        self.api.get(f"/multiaccess/memberbooth/member/{member.member_number}").expect(
            200,
            data__keys=[],
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )

    def test_memberbooth_can_get_member_by_number(self) -> None:
        assert self.api is not None
        member: Member = self.db.create_member()
        key: Key = self.db.create_key()

        response: ApiResponse = self.api.get(f"/multiaccess/memberbooth/member/{member.member_number}")
        response.expect(
            200,
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )
        self.assertNotEqual([], response.data["keys"], "There exists keys")

    def test_memberbooth_can_get_member_by_tag(self) -> None:
        assert self.api is not None
        member: Member = self.db.create_member()
        key: Key = self.db.create_key()

        response: ApiResponse = self.api.get(f"/multiaccess/memberbooth/tag/{key.tagid}")
        response.expect(
            200,
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )
        self.assertNotEqual([], response.data["keys"], "There exists keys")

    def test_cannot_get_member_without_pin_set(self) -> None:
        assert self.api is not None
        member: Member = self.db.create_member()  # Defaults without PIN

        self.api.post(
            "/multiaccess/memberbooth/pin-login",
            json=dict(member_number=member.member_number, pin_code=member.pin_code),
        ).is_not_ok()
        self.api.post(
            "/multiaccess/memberbooth/pin-login", json=dict(member_number=member.member_number, pin_code="")
        ).is_not_ok()

    def test_get_member_with_pin(self) -> None:
        assert self.api is not None
        member: Member = self.db.create_member(pin_code=1234)

        response: ApiResponse = self.api.post(
            "/multiaccess/memberbooth/pin-login",
            json=dict(member_number=member.member_number, pin_code=member.pin_code),
        )
        response.expect(200)

        response = self.api.post(
            "/multiaccess/memberbooth/pin-login", json=dict(member_number=member.member_number, pin_code="wrong pin")
        )
        response.expect(404)
