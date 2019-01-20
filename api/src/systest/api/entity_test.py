from datetime import datetime
from random import randint

from service.api_definition import REQUIRED, NOT_UNIQUE
from test_aid.systest_base import ApiTest
from test_aid.test_util import random_str


class Test(ApiTest):
    
    def test_create_and_get(self):
        entity = self.obj.create_group()
        entity_id = self\
            .post("/membership/group", entity)\
            .expect(code=201, status="created", data=entity)\
            .get('data__group_id')

        self.assertTrue(entity_id)

        data = self.get(f"/membership/group/{entity_id}").expect(code=200, data=entity, data__group_id=entity_id).data
        
        self.assertIsNotNone(data['created_at'])
        self.assertIsNone(data['updated_at'])
        self.assertIsNone(data['deleted_at'])

    def test_can_not_create_with_empty_data(self):
        self.post("/membership/group", dict()).expect(code=422)
        self.post("/membership/group", dict(group_id=1, created_at='remove_me')).expect(code=422)

    def test_update(self):
        entity = self.api.create_group()
        entity_id = entity['group_id']

        self.assertIsNone(entity['updated_at'])

        data = self\
            .put(f"/membership/group/{entity_id}", dict(name='arne'))\
            .expect(code=200, data__name='arne', data__group_id=entity_id)\
            .data
        
        self.assertTrue(data['updated_at'] >= data['created_at'])

    def test_can_not_update_entity_using_empty_or_read_only_data(self):
        entity = self.api.create_group()
        entity_id = entity['group_id']

        self.put(f"/membership/group/{entity_id}", dict()).expect(code=422)
        self.put(f"/membership/group/{entity_id}", dict(group_id=1, deleted_at='remove_me')).expect(code=422)

    def test_list(self):
        before = self.get("/membership/group?page_size=0").get('data')
        
        entity1_id = self.api.create_group()['group_id']
        entity2_id = self.api.create_group()['group_id']

        ids_before = {e['group_id'] for e in before}
        self.assertNotIn(entity1_id, ids_before)
        self.assertNotIn(entity2_id, ids_before)

        after = self.get("/membership/group?page_size=0").get('data')

        ids_after = {e['group_id'] for e in after}
        self.assertIn(entity1_id, ids_after)
        self.assertIn(entity2_id, ids_after)

    def test_deleted_entity_does_not_show_up_in_list_but_can_still_be_fetched(self):
        entity_id = self.api.create_group()['group_id']
        
        self.assertIn(entity_id, [e['group_id'] for e in self.get("/membership/group?page_size=0").data])
        
        self.delete(f"/membership/group/{entity_id}").expect(code=200, status="deleted")
        
        self.assertNotIn(entity_id, [e['group_id'] for e in self.get("/membership/group").data])

        data = self.get(f"/membership/group/{entity_id}").expect(code=200, data__group_id=entity_id).data
        
        self.assertTrue(data['deleted_at'] >= data['created_at'])

    def test_list_deleted_entity_show_up_if_list_deleted_is_true_for_entity(self):
        self.db.create_member()
        span = self.db.create_span(deleted_at=self.datetime())
        self.assertIn(span.span_id, [e['span_id'] for e in self.get("/membership/span?page_size=0").data])

    def test_primary_key__created_at_and_updated_at_is_filtered_on_update(self):
        entity = self.api.create_group()
        entity_id = entity['group_id']

        t = datetime(2017, 1, 1).isoformat()

        data = self\
            .put(f"/membership/group/{entity_id}", dict(name='new_name', group_id=entity_id + 1,
                                                        created_at=t, updated_at=t))\
            .expect(code=200).data
        
        self.assertTrue(datetime.fromisoformat(data['updated_at']).year > 2017)
        self.assertTrue(datetime.fromisoformat(data['created_at']).year > 2017)
        self.assertEqual(entity_id, data['group_id'])
        self.assertEqual('new_name', data['name'])

        self.get(f"/membership/group/{entity_id}").expect(code=200, data__group_id=entity_id)

    def test_unique_constraint_fails_with_message(self):
        entity_1 = self.obj.create_member()
        email = entity_1['email']
        entity_2 = self.obj.create_member(email=email)
        
        self.post("/membership/member", entity_1).expect(code=201)
        self.post("/membership/member", entity_2).expect(code=422, what=NOT_UNIQUE, fields='email')
        
    def test_not_null_constraint_fails_with_message(self):
        member = self.obj.create_member()
        member.pop('email', None)
        
        self.post("/membership/member", member).expect(code=422, what=REQUIRED, fields='email')
    
    def test_search_for_text(self):
        entity = self.api.create_group()
        entity_id = entity['group_id']
        
        result = self.get(f"/membership/group?search={entity['title']}").expect(code=200, page=1, total=1).data[0]
        
        self.assertEqual(entity_id, result['group_id'])

        self.get(f"/membership/group?search={random_str()}").expect(code=200, page=1, total=0, data=[])
    
    def test_search_for_number_column_works(self):
        entity = self.api.create_member(member_number=randint(1e8, 9e8))
        entity_id = entity['member_id']
        
        result = self.get(f"/membership/member?search={entity['member_number']}").expect(code=200).data[0]
        
        self.assertEqual(entity_id, result['member_id'])

        self.get(f"/membership/group?search={randint(1e8, 9e8)}").expect(code=200, page=1, total=0, data=[])
        
    def test_pagination_and_sort(self):
        firstname = random_str(12)
        entity1 = self.api.create_member(firstname=firstname, lastname="d")
        entity2 = self.api.create_member(firstname=firstname, lastname="c")
        entity3 = self.api.create_member(firstname=firstname, lastname="a")
        entity4 = self.api.create_member(firstname=firstname, lastname="b")
        
        entity1_id = entity1['member_id']
        entity2_id = entity2['member_id']
        entity3_id = entity3['member_id']
        entity4_id = entity4['member_id']
        
        result = self\
            .get(f"/membership/member?search={firstname}&sort_by=lastname&sort_order=asc&page_size=2")\
            .expect(code=200, page=1, per_page=2, last_page=2, total=4)\
            .data
        
        self.assertEqual([entity3_id, entity4_id], [e['member_id'] for e in result])

        result = self\
            .get(f"/membership/member?search={firstname}&sort_by=lastname&sort_order=asc&page_size=2&page=2")\
            .expect(code=200, page=2, per_page=2, last_page=2, total=4)\
            .data
        
        self.assertEqual([entity2_id, entity1_id], [e['member_id'] for e in result])
        
        result = self\
            .get(f"/membership/member?search={firstname}&sort_by=lastname&sort_order=desc&page_size=3&page=1")\
            .expect(code=200, page=1, per_page=3, last_page=2, total=4)\
            .data
        
        self.assertEqual([entity1_id, entity2_id, entity4_id], [e['member_id'] for e in result])

        result = self\
            .get(f"/membership/member?search={firstname}&sort_by=lastname&sort_order=desc&page_size=3&page=2")\
            .expect(code=200, page=2, per_page=3, last_page=2, total=4)\
            .data
        
        self.assertEqual([entity3_id], [e['member_id'] for e in result])
        
        self.get(f"/membership/member?search={firstname}&sort_by=lastname&sort_order=desc&page_size=3&page=0")\
            .expect(code=422)

        self.get(f"/membership/member?search={firstname}&sort_by=lastname&sort_order=desc&page_size=3&page=3")\
            .expect(code=200, data=[], page=3, per_page=3, last_page=2, total=4)

    # TODO Is delete non existent 404 or 200?
    