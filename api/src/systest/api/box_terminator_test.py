from random import randint
from unittest import skip

from membership.models import Box, Span
from messages.models import Message
from service.db import db_session
from test_aid.systest_base import ApiTest


class Test(ApiTest):
#TODO add nag db tests
#TODO add more nag email tests
#TODO check status test, including with pending labaccess days
#TODO more list all storage tests with filters
    
    def test_box_terminator_validate_creates_box_if_not_exists(self):
        member = self.db.create_member()
        label_id = randint(1e9, 9e9)
        storage_type='box'
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, storage_type=storage_type label_id=label_id)).expect(
            200,
            data__member_number=member.member_number,
            data__expire_date='1997-09-27',
            data__terminate_date='1997-11-11',
            data__storage_type=storage_type
            data__status='terminate'
        )
        
        db_session.close()
        
        item = db_session.query(MemberStorage).filter_by(label_id=label_id).one()
        
        self.assertIsNone(item.last_nag_at)
        self.assertIsNotNone(item.last_check_at)

    def test_box_terminator_validate_uses_existing_box_if_it_exists(self):
        member = self.db.create_member()
        item = self.db.create_member_storage('box')
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, label_id=item.label_id)).expect(200)
        
        db_session.close()
        
        db_item = db_session.query(MemberStorage).filter_by(member_id=member.member_id).one()
        
        self.assertEqual(item.label_id, db_item.label_id)
        self.assertIsNone(db_item.last_nag_at)
        self.assertIsNotNone(db_item.last_check_at)

    def test_box_terminator_validate_status_terminate(self):
        member = self.db.create_member()
        item = self.db.create_member_storage('box')
        span = self.db.create_span(enddate=self.date(-50), type=Span.LABACCESS)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, label_id=item.label_id)).expect(
            200,
            data__expire_date=self.date(-50 + 1).isoformat(),
            data__terminate_date=self.date(-50 + 45 + 1).isoformat(),
            data__status='terminate'
        )

    def test_box_terminator_validate_status_expired(self):
        member = self.db.create_member()
        item = self.db.create_member_storage('box')
        span = self.db.create_span(enddate=self.date(-10), type=Span.LABACCESS)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, label_id=item.label_id)).expect(
            200,
            data__expire_date=self.date(-10 + 1).isoformat(),
            data__terminate_date=self.date(-10 + 45 + 1).isoformat(),
            data__status='expired'
        )

    def test_box_terminator_validate_status_active(self):
        member = self.db.create_member()
        item = self.db.create_member_storage('box')
        span = self.db.create_span(enddate=self.date(10), type=Span.LABACCESS)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, label_id=box.label_id)).expect(
            200,
            data__expire_date=self.date(10 + 1).isoformat(),
            data__terminate_date=self.date(10 + 45 + 1).isoformat(),
            data__status='active'
        )

    def test_box_terminator_validate_deleted_span_is_filtered(self):
        member = self.db.create_member()
        item = self.db.create_member_storage('box')
        span = self.db.create_span(enddate=self.date(10), type=Span.LABACCESS, deleted_at=self.datetime())
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, label_id=item.label_id)).expect(
            200,
            data__status='terminate'
        )

    def test_box_terminator_validate_membership_span_is_filtered(self):
        member = self.db.create_member()
        item = self.db.create_member_storage('box')
        span = self.db.create_span(enddate=self.date(10), type=Span.MEMBERSHIP)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, label_id=item.label_id)).expect(
            200,
            data__status='terminate'
        )
    
    def test_box_terminator_send_nag_email(self):
        member = self.db.create_member()
        item = self.db.create_member_storage('box')
        
        self.api.post('/multiaccess/box-terminator/nag',
                      dict(member_number=member.member_number, label_id=item.label_id, nag_type="nag-warning"))\
             .expect(200)
        
        db_session.close()
        
        message = db_session.query(Message).filter_by(member_id=member.member_id).one()
        
        self.assertIn('lådan', message.body) #TODO improve

    def test_box_terminator_list_all_boxes(self):
        token = self.db.create_access_token()

        member1 = self.db.create_member()
        item11 = self.db.create_member_storage('box')
        item12 = self.db.create_member_storage('box')

        member2 = self.db.create_member()
        item21 = self.db.create_member_storage('box')
        
        self.api.post('/multiaccess/box-terminator/validate', token=token.access_token,
                      json=dict(member_number=member1.member_number, box_label_id=box11.box_label_id)).expect(200)

        self.api.post('/multiaccess/box-terminator/validate', token=token.access_token,
                      json=dict(member_number=member1.member_number, box_label_id=box12.box_label_id)).expect(200)

        self.api.post('/multiaccess/box-terminator/validate', token=token.access_token,
                      json=dict(member_number=member2.member_number, box_label_id=box21.box_label_id)).expect(200)
        
        data = self.api.get('/multiaccess/box-terminator/stored_items', token=token.access_token).expect(200).data
    
        item_ids = [b['label_id'] for b in data]
    
        self.assertIn(item11.label_id, item_ids)
        self.assertIn(item12.label_id, item_ids)
        self.assertIn(item21.label_id, item_ids)
    
