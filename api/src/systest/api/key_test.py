from test_aid.systest_base import ApiTest


class Test(ApiTest):
    def test_get_keys_for_member(self):
        member = self.db.create_member()
        key1 = self.api.create_key(member_id=member.member_id)
        key2 = self.api.create_key(member_id=member.member_id)

        data = self.get(f"/membership/member/{member.member_id}/keys").expect(code=200).print().data

        self.assertCountEqual([key1["key_id"], key2["key_id"]], [k["key_id"] for k in data])

    def test_create_key_with_existing_tagid_fails(self):
        member = self.db.create_member()
        key = self.obj.create_key(member_id=member.member_id)
        self.post("/membership/key", json=key).expect(code=201)
        self.post("/membership/key", json=key).expect(code=422, status="error", what="not_unique", fields="tagid")
