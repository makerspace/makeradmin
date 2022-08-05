from random import randint

from test_aid.systest_base import ApiTest


class Test(ApiTest):
    
    def test_basic_operations(self):
        related_entity = self.api.create_group()
        related_entity_id = related_entity['group_id']
        
        entity_1 = self.api.create_member()
        entity_1_id = entity_1['member_id']

        entity_2 = self.api.create_member()
        entity_2_id = entity_2['member_id']
        
        self.get(f"/membership/group/{related_entity_id}/members").expect(code=200, data=[])

        self.post(f"/membership/group/{related_entity_id}/members/add", {'members': [entity_1_id, entity_2_id]})\
            .expect(code=200)

        data = self.get(f"/membership/group/{related_entity_id}/members").expect(code=200, total=2).get('data')
        
        self.assertCountEqual([entity_1_id, entity_2_id], [m['member_id'] for m in data])

        self.post(f"/membership/group/{related_entity_id}/members/remove", {'members': [entity_2_id]}).expect(code=200)

        data = self.get(f"/membership/group/{related_entity_id}/members").expect(code=200, total=1).get('data')

        self.assertCountEqual([entity_1_id], [m['member_id'] for m in data])

    def test_adding_non_existing_entities_is_ok(self):
        related_entity = self.api.create_group()
        related_entity_id = related_entity['group_id']

        self.post(f"/membership/group/{related_entity_id}/members/add", {'members': [randint(int(1e8), int(9e8))]})\
            .expect(code=200)

        self.get(f"/membership/group/{related_entity_id}/members").expect(code=200, data=[])

    def test_removing_non_existing_entities_is_ok(self):
        related_entity = self.api.create_group()
        related_entity_id = related_entity['group_id']

        self.post(f"/membership/group/{related_entity_id}/members/remove", {'members': [randint(int(1e8), int(9e8))]})\
            .expect(code=200)
