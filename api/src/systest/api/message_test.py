from random import randint

from messages.models import Recipient, Message
from service.db import db_session
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.group = self.api.create_group()
        self.group_id = self.group['group_id']
        
        self.member_1 = self.api.create_member()
        self.member_1_id = self.member_1['member_id']

        self.member_2 = self.api.create_member()
        self.member_2_id = self.member_2['member_id']

        self.api.post(f"/membership/group/{self.group_id}/members/add",
                      {'members': [self.member_1_id, self.member_2_id]}).expect(code=200)

        self.member_3 = self.api.create_member()
        self.member_3_id = self.member_3['member_id']

    def test_message_recipient_count_in_get(self):
        message = self.db.create_message()
        
        self.api.get(f"/messages/message/{message.messages_message_id}").expect(200, data__num_recipients=0)
        
        member = self.db.create_member()
        self.db.create_recipient(messages_message_id=message.messages_message_id, member_id=member.member_id)
        
        member = self.db.create_member()
        self.db.create_recipient(messages_message_id=message.messages_message_id, member_id=member.member_id)
        
        self.api.get(f"/messages/message/{message.messages_message_id}").expect(200, data__num_recipients=2)

    def test_queue_message_for_sending_with_member_recipient_list(self):
        message = self.obj.create_message()
        message['recipients'] = [{'id': self.member_1_id, 'type': 'member'}]
        
        message_id = self.api.post("/messages/message", message).expect(201).get('data__messages_message_id')
        
        db_message = db_session.query(Message).get(message_id)
        
        self.assertEqual('queued', db_message.status)
        self.assertEqual(message['description'], db_message.description)
        self.assertEqual(message['title'], db_message.title)
        
        db_recipients = db_session.query(Recipient).filter_by(messages_message_id=db_message.messages_message_id).all()
        
        self.assertCountEqual([self.member_1['email']], [r.recipient for r in db_recipients])
        self.assertCountEqual([self.member_1_id], [r.member_id for r in db_recipients])
        self.assertEqual({'queued'}, {r.status for r in db_recipients})
        self.assertEqual({message['title']}, {r.title for r in db_recipients})
        self.assertEqual({message['description']}, {r.description for r in db_recipients})

    def test_queue_message_for_sending_with_group_recipient_list(self):
        message = self.obj.create_message()
        message['recipients'] = [{'id': self.group_id, 'type': 'group'}]
        
        message_id = self.api.post("/messages/message", message).expect(201).get('data__messages_message_id')
        
        db_message = db_session.query(Message).get(message_id)
        
        self.assertEqual('queued', db_message.status)
        self.assertEqual(message['description'], db_message.description)
        self.assertEqual(message['title'], db_message.title)
        
        db_recipients = db_session.query(Recipient).filter_by(messages_message_id=db_message.messages_message_id).all()
        
        self.assertCountEqual([self.member_1['email'], self.member_2['email']], [r.recipient for r in db_recipients])
        self.assertCountEqual([self.member_1_id, self.member_2_id], [r.member_id for r in db_recipients])
        self.assertEqual({'queued'}, {r.status for r in db_recipients})
        self.assertEqual({message['title']}, {r.title for r in db_recipients})
        self.assertEqual({message['description']}, {r.description for r in db_recipients})

    def test_queue_message_for_sending_with_group_and_member_recipient_list(self):
        message = self.obj.create_message()
        message['recipients'] = [
            {'id': self.group_id, 'type': 'group'},
            {'id': self.member_2_id, 'type': 'member'},
            {'id': self.member_3_id, 'type': 'member'},
        ]
        
        message_id = self.api.post("/messages/message", message).expect(201).get('data__messages_message_id')
        
        db_message = db_session.query(Message).get(message_id)
        
        self.assertEqual('queued', db_message.status)
        self.assertEqual(message['description'], db_message.description)
        self.assertEqual(message['title'], db_message.title)
        
        db_recipients = db_session.query(Recipient).filter_by(messages_message_id=db_message.messages_message_id).all()
        
        self.assertCountEqual([self.member_1['email'], self.member_2['email'], self.member_3['email']],
                              [r.recipient for r in db_recipients])
        self.assertCountEqual([self.member_1_id, self.member_2_id, self.member_3_id],
                              [r.member_id for r in db_recipients])
        self.assertEqual({'queued'}, {r.status for r in db_recipients})
        self.assertEqual({message['title']}, {r.title for r in db_recipients})
        self.assertEqual({message['description']}, {r.description for r in db_recipients})

    def test_queue_message_with_template_replacement(self):
        message = self.obj.create_message(title="##member_number## ##member_id## ##firstname## ##lastname## ##email##")
        message['recipients'] = [{'id': self.member_1_id, 'type': 'member'}]
        
        message_id = self.api.post("/messages/message", message).expect(201).get('data__messages_message_id')
        
        db_message = db_session.query(Message).get(message_id)
        
        self.assertEqual(message['title'], db_message.title)
        
        db_recipient = db_session.query(Recipient).filter_by(messages_message_id=db_message.messages_message_id).one()
        
        self.assertEqual(f"{self.member_1['member_number']} {self.member_1['member_id']} {self.member_1['firstname']}"
                         f" {self.member_1['lastname']} {self.member_1['email']}",
                         db_recipient.title)

    def test_send_message_to_non_member_does_not_work(self):
        message = self.obj.create_message()
        message['recipients'] = [{'id': randint(1e9, 9e9), 'type': 'member'}]
        
        self.api.post("/messages/message", message).expect(422)

