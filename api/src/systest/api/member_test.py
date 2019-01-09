from random import randint

from test_aid.systest_base import ApiTest


class Test(ApiTest):
    # Tests for members that are not covered by entity tests.
    
    def test_create_member_with_existing_email_fails(self):
        member = self.obj.create_member()
        member_number = self.post("/membership/member", json=member).expect(code=201).get('data__member_number')
        member['member_number'] = member_number + 1000
        self.post("/membership/member", json=member).expect(code=422, status="error", what="not_unique",
                                                            fields='email')

    def test_create_member_with_existing_member_number_fails(self):
        member = self.obj.create_member()
        member_number = self.post("/membership/member", json=member).expect(code=201).get('data__member_number')
        member['email'] = member['email'] + '-not-duplicate'
        member['member_number'] = member_number
        self.post("/membership/member", json=member).expect(code=422, status="error", what="not_unique",
                                                            fields='member_number')

    def test_create_member_gives_new_member_numbers_and_ids(self):
        member1 = self.obj.create_member()
        member2 = self.obj.create_member()
        
        id1, number1 = \
            self.post("/membership/member", json=member1).expect(code=201).get('data__member_id', 'data__member_number')
        
        id2, number2 = \
            self.post("/membership/member", json=member2).expect(code=201).get('data__member_id', 'data__member_number')
        
        self.assertNotEqual(id1, id2)
        self.assertNotEqual(number1, number2)
        
    def test_include_membership_in_member_get(self):
        # TODO BM We need to be able to create spans with api or db to do this test.
        pass

    def test_include_membership_in_member_list(self):
        # TODO BM We need to be able to create spans with api or db to do this test. Or is this a special endpoint,
        # only used in one place.
        pass
