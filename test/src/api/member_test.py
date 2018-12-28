from aid.test.api import ApiTest


class Test(ApiTest):
    
    def test_create_and_get_member(self):
        member = self.obj.create_member()
        
        member_id, member_number = self\
            .post("/membership/member", json=member)\
            .expect(code=201, data=member)\
            .get('data__member_id', 'data__member_number')
        
        self.assertTrue(member_id)
        self.assertTrue(member_number)
        
        self.get(f"/membership/member/{member_id}").expect(code=200, data=member, data__member_id=member_id)
    
    def test_create_member_with_existing_email_fails(self):
        member = self.obj.create_member()
        self.post("/membership/member", json=member).expect(code=201)
        self.post("/membership/member", json=member).expect(code=422, status="error", column="email")

    def test_create_member_gives_new_member_numbers_and_ids(self):
        member1 = self.obj.create_member()
        member2 = self.obj.create_member()
        
        id1, number1 = \
            self.post("/membership/member", json=member1).expect(code=201).get('data__member_id', 'data__member_number')
        
        id2, number2 = \
            self.post("/membership/member", json=member2).expect(code=201).get('data__member_id', 'data__member_number')
        
        self.assertNotEqual(id1, id2)
        self.assertNotEqual(number1, number2)

    def test_update_member(self):
        member = self.obj.create_member()
        
        member_id = self.post("/membership/member", json=member).expect(code=201).get('data__member_id')
        self.get(f"/membership/member/{member_id}").expect(code=200, data__firstname=member['firstname'])
        self.put(f"/membership/member/{member_id}", json={**member, 'firstname': 'Kuno'}).expect(code=200)
        self.get(f"/membership/member/{member_id}").expect(code=200, data__firstname='Kuno')

    def test_list_members(self):
        before = self.get("/membership/member").get('data')

        member1_id = self.api.create_member()['member_id']
        member2_id = self.api.create_member()['member_id']

        ids_before = {m['member_id'] for m in before}
        self.assertNotIn(member1_id, ids_before)
        self.assertNotIn(member2_id, ids_before)

        after = self.get("/membership/member").get('data')

        ids_after = {m['member_id'] for m in after}
        self.assertIn(member1_id, ids_after)
        self.assertIn(member2_id, ids_after)

    def test_deleted_members_does_not_show_up_in_list(self):
        member_id = self.api.create_member()['member_id']
        
        before = self.get("/membership/member").get('data')
        self.assertIn(member_id, {m['member_id'] for m in before})
        
        self.delete(f"/membership/member/{member_id}").expect(code=200)
        
        after = self.get("/membership/member").get('data')
        self.assertNotIn(member_id, {m['member_id'] for m in after})

    def test_deleted_member_can_still_be_retrieved(self):
        member = self.api.create_member()
        member_id = member['member_id']
        
        self.delete(f"/membership/member/{member_id}").expect(code=200)
        
        member.pop("deleted_at")
        self.assertIsNotNone(self
                             .get(f"/membership/member/{member_id}")
                             .expect(code=200, data=member)
                             .get('data__deleted_at'))
        
        