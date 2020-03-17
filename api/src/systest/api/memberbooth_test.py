from test_aid.systest_base import ApiTest


class Test(ApiTest):
    
    def test_memberbooth_can_get_member_by_number_even_if_member_does_not_have_a_key(self):
        member = self.db.create_member()
        
        self.api.get('/multiaccess/memberbooth/member', params=dict(member_number=member.member_number)).expect(
            200,
            data__keys=[],
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )

    def test_memberbooth_can_get_member_by_number(self):
        member = self.db.create_member()
        key = self.db.create_key()
        
        response = self.api.get('/multiaccess/memberbooth/member', params=dict(member_number=member.member_number))
        response.expect(
            200,
            data__firstname=member.firstname,
            data__member_id=member.member_id,
        )
        self.assertNotEqual([], response.data["keys"], "There exists keys")
