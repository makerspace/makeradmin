from membership.models import Span
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    
    def test_included_if_has_labaccess_span(self):
        member = self.db.create_member()
        key = self.db.create_key(member=member)
        self.db.create_span(member=member, startdate=self.date(-10), enddate=self.date(-5), type=Span.LABACCESS)
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        
        res = next(m for m in data if m['member_id'] == member.member_id)
        
        self.assertEqual({
            'member_id': member.member_id,
            'member_number': member.member_number,
            'firstname': member.firstname,
            'lastname': member.lastname,
            'end_date': self.date(-5).isoformat(),
            'keys': [{'key_id': key.key_id, 'rfid_tag': key.tagid}],
            }, res)
        
    def test_included_if_has_special_labaccess_span(self):
        member = self.db.create_member()
        self.db.create_key(member=member)
        self.db.create_span(member=member, startdate=self.date(-10), enddate=self.date(10), type=Span.SPECIAL_LABACESS)
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        self.assertIn(member.member_id, [m['member_id'] for m in data])
    
    def test_included_if_has_multiple_keys(self):
        member = self.db.create_member()
        self.db.create_span(member=member, type=Span.LABACCESS)
        key1 = self.db.create_key(member=member)
        key2 = self.db.create_key(member=member)
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        
        res = next(m for m in data if m['member_id'] == member.member_id)
        
        self.assertCountEqual([
            {'key_id': key1.key_id, 'rfid_tag': key1.tagid},
            {'key_id': key2.key_id, 'rfid_tag': key2.tagid},
        ], res['keys'])
    
    def test_not_included_if_has_no_span(self):
        member = self.db.create_member()
        self.db.create_key(member=member)
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        self.assertNotIn(member.member_id, [m['member_id'] for m in data])
    
    def test_not_included_if_has_no_key(self):
        member = self.db.create_member()
        self.db.create_span(member=member)
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        self.assertNotIn(member.member_id, [m['member_id'] for m in data])
    
    def test_not_included_if_has_only_deleted_span(self):
        member = self.db.create_member()
        self.db.create_key(member=member)
        self.db.create_span(member=member, deleted_at=self.datetime())
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        self.assertNotIn(member.member_id, [m['member_id'] for m in data])
    
    def test_not_included_if_has_only_membership_span(self):
        member = self.db.create_member()
        self.db.create_key(member=member)
        self.db.create_span(member=member, type=Span.MEMBERSHIP)
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        self.assertNotIn(member.member_id, [m['member_id'] for m in data])
    
    def test_not_included_if_has_only_deleted_key(self):
        member = self.db.create_member()
        self.db.create_key(member=member, deleted_at=self.datetime())
        self.db.create_span(member=member)
        data = self.api.get('/multiaccess/memberdata').expect(200).get('data')
        self.assertNotIn(member.member_id, [m['member_id'] for m in data])
