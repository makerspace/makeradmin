from test_aid.systest_base import ApiTest


class Test(ApiTest):
    
    def test_message_recipiten_count_in_get(self):
        message = self.db.create_message()
        
        self.api.get(f"/messages/message/{message.messages_message_id}").expect(200, data__num_recipients=0)
        
        member = self.db.create_member()
        self.db.create_recipient(messages_message_id=message.messages_message_id, member_id=member.member_id)
        
        member = self.db.create_member()
        self.db.create_recipient(messages_message_id=message.messages_message_id, member_id=member.member_id)
        
        self.api.get(f"/messages/message/{message.messages_message_id}").expect(200, data__num_recipients=2)
