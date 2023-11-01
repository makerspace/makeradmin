from random import randint

from messages.models import Message
from service.db import db_session
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.group = self.api.create_group()
        self.group_id = self.group["group_id"]

        self.member_1 = self.api.create_member()
        self.member_1_id = self.member_1["member_id"]

        self.member_2 = self.api.create_member()
        self.member_2_id = self.member_2["member_id"]

        self.api.post(
            f"/membership/group/{self.group_id}/members/add", {"members": [self.member_1_id, self.member_2_id]}
        ).expect(code=200)

        self.member_3 = self.api.create_member()
        self.member_3_id = self.member_3["member_id"]

    def test_queue_message_for_sending_with_member_recipient_list(self):
        message = self.obj.create_message()
        message["recipients"] = [{"id": self.member_1_id, "type": "member"}]

        self.api.post("/messages/message", message).expect(201)

        db_messages = db_session.query(Message).filter_by(subject=message["subject"]).all()

        self.assertCountEqual([self.member_1["email"]], [m.recipient for m in db_messages])
        self.assertCountEqual([self.member_1_id], [m.member_id for m in db_messages])
        self.assertEqual({"queued"}, {m.status for m in db_messages})
        self.assertEqual({message["subject"]}, {m.subject for m in db_messages})
        self.assertEqual({message["body"]}, {m.body for m in db_messages})

    def test_queue_message_for_sending_with_group_recipient_list(self):
        message = self.obj.create_message()
        message["recipients"] = [{"id": self.group_id, "type": "group"}]

        self.api.post("/messages/message", message).expect(201)

        db_messages = db_session.query(Message).filter_by(subject=message["subject"]).all()

        self.assertCountEqual([self.member_1["email"], self.member_2["email"]], [m.recipient for m in db_messages])
        self.assertCountEqual([self.member_1_id, self.member_2_id], [m.member_id for m in db_messages])
        self.assertEqual({"queued"}, {m.status for m in db_messages})
        self.assertEqual({message["subject"]}, {m.subject for m in db_messages})
        self.assertEqual({message["body"]}, {m.body for m in db_messages})

    def test_queue_message_for_sending_with_group_and_member_recipient_list(self):
        message = self.obj.create_message()
        message["recipients"] = [
            {"id": self.group_id, "type": "group"},
            {"id": self.member_2_id, "type": "member"},
            {"id": self.member_3_id, "type": "member"},
        ]

        self.api.post("/messages/message", message).expect(201)

        db_messages = db_session.query(Message).filter_by(subject=message["subject"]).all()

        self.assertCountEqual(
            [self.member_1["email"], self.member_2["email"], self.member_3["email"]], [m.recipient for m in db_messages]
        )
        self.assertCountEqual(
            [self.member_1_id, self.member_2_id, self.member_3_id], [m.member_id for m in db_messages]
        )
        self.assertEqual({"queued"}, {m.status for m in db_messages})
        self.assertEqual({message["subject"]}, {m.subject for m in db_messages})
        self.assertEqual({message["body"]}, {m.body for m in db_messages})

    def test_send_message_to_non_member_does_not_work(self):
        message = self.obj.create_message()
        message["recipients"] = [{"id": randint(int(1e9), int(9e9)), "type": "member"}]

        self.api.post("/messages/message", message).expect(422)
