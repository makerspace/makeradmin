from library.base import ApiTest
from library.factory import GroupFactory


class Test(ApiTest):
    
    def test_create_and_get(self):
        group = GroupFactory()
        


    def test_groups(self):
        # TODO 
        return 
        
        ''' Test various things to do with groups '''
        previous_groups = self.get(f"membership/group", 200)["data"]

        with MemberDummies(self, 10) as created_members:
            groups = [{
                "name": "science_group" + str(i),
                "title": "Aperture Science Volounteer Group",
                "description": "Volounteers for being exposed to neurotoxin",
            } for i in range(10)]

            created_groups = [
                self.post("membership/group", group, 201, expected_result={"status": "created", "data": group})["data"]
                for group in groups
            ]

            # Make sure the get method returns the same result as the post method
            for group in created_groups:
                self.get(f"membership/group/{group['group_id']}", 200, expected_result={"data": group})

            # List all groups
            # Inconsistency: list views do not include entity_id
            self.get(f"membership/group?sort_by=group_id&sort_order=asc", 200, expected_result={"data": previous_groups + list(map(strip_entity_id, created_groups))})

            for (member, password), group in zip(created_members, created_groups):
                member_id = member["member_id"]
                group_id = group["group_id"]

                self.post(f"membership/member/{member_id}/groups/add", {"groups": [group_id]}, 200, expected_result={"status": "ok"})

                # Inconsistency: list views do not include entity_id
                group2 = strip_entity_id(group)

                member2 = strip_entity_id(member)

                # Make sure the member has been added to the group
                self.get(f"membership/member/{member_id}/groups", 200, expected_result={"data": [group2]})
                self.get(f"membership/group/{group_id}/members", 200, expected_result={"data": [member2]})

                # Remove the member from the group
                self.post(f"membership/member/{member_id}/groups/remove", {"groups": [group_id]}, 200, expected_result={"status": "ok"})

                # Make sure the member has been removed from the group
                self.get(f"membership/member/{member_id}/groups", 200, expected_result={"data": []})

            for group in created_groups:
                self.delete(f"membership/group/{group['group_id']}", 200, expected_result={"status": "deleted"})
                # Note that deleted groups still show up when explicitly accessed, but they should not show up in lists (this is checked for below)
                self.get(f"membership/group/{group['group_id']}", 200, expected_result={"data": group})

            # Make sure all groups have been deleted
            self.get(f"membership/group", 200, expected_result={"data": previous_groups})

