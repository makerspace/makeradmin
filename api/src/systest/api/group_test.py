from test_aid.systest_base import ApiTest


class Test(ApiTest):
    
    def test_create_and_get(self):
        group = self.obj.create_group()
        group_id = self\
            .post("/membership/group", group)\
            .expect(code=201, status="created", data=group)\
            .get('data__group_id')

        self.assertTrue(group_id)

        self.get(f"/membership/group/{group_id}").expect(code=200, data=group, data__group_id=group_id)

    def test_list_groups(self):
        before = self.get("/membership/group").get('data')
        
        group1_id = self.api.create_group()['group_id']
        group2_id = self.api.create_group()['group_id']

        ids_before = {g['group_id'] for g in before}
        self.assertNotIn(group1_id, ids_before)
        self.assertNotIn(group2_id, ids_before)

        after = self.get("/membership/group?page_size=0").get('data')

        ids_after = {g['group_id'] for g in after}
        self.assertIn(group1_id, ids_after)
        self.assertIn(group2_id, ids_after)

    def test_add_and_remove_member_in_group(self):
        member_id = self.api.create_member()['member_id']
        group_id = self.api.create_group()['group_id']

        self.get(f"/membership/member/{member_id}/groups").expect(code=200, data=[])
        self.get(f"/membership/group/{group_id}/members").expect(code=200, data=[])

        self.post(f"/membership/member/{member_id}/groups/add", {"groups": [group_id]}).expect(code=200, status='ok')

        self.assertEqual([group_id],
                         [g['group_id'] for g in
                          self.get(f"/membership/member/{member_id}/groups").expect(code=200).data])

        self.assertEqual([member_id],
                         [m['member_id'] for m in
                          self.get(f"/membership/group/{group_id}/members").expect(code=200).data])

        self.post(f"/membership/member/{member_id}/groups/remove", {"groups": [group_id]}).expect(code=200, status="ok")
        
        self.get(f"/membership/member/{member_id}/groups").expect(code=200, data=[])
        self.get(f"/membership/group/{group_id}/members").expect(code=200, data=[])

    # TODO BM Test permissions.
