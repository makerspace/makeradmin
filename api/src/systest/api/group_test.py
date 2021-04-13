from test_aid.systest_base import ApiTest


class Test(ApiTest):
    
    def test_group_member_count_in_list(self):
        group = self.api.create_group()
        group_id = group['group_id']
        
        data = self.api.get(f"/membership/group?search={group['name']}").expect(200).data
        self.assertEqual(0, data[0]['num_members'])

        member1_id = self.api.create_member()['member_id']
        member2_id = self.api.create_member()['member_id']
        
        self.api.post(f"/membership/group/{group_id}/members/add", {'members': [member1_id, member2_id]}).expect(200)

        data = self.api.get(f"/membership/group?search={group['name']}").expect(200).data
        self.assertEqual(2, data[0]['num_members'])
