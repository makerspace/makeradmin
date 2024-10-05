from datetime import datetime, timezone
from random import randint
from unittest import skip

from membership.models import Box, Span
from messages.models import Message
from service.db import db_session
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    def test_box_terminator_validate_creates_box_if_not_exists(self):
        member = self.db.create_member()
        box_label_id = randint(int(1e9), int(9e9))

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            dict(member_number=member.member_number, box_label_id=box_label_id),
        ).expect(
            200,
            data__member_number=member.member_number,
            data__expire_date="1997-09-27",
            data__terminate_date="1997-11-11",
            data__status="terminate",
        )

        db_session.close()

        box = db_session.query(Box).filter_by(box_label_id=box_label_id).one()

        self.assertIsNone(box.last_nag_at)
        self.assertIsNotNone(box.last_check_at)

    def test_box_terminator_validate_uses_existing_box_if_it_exists(self):
        member = self.db.create_member()
        box = self.db.create_box()

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            dict(member_number=member.member_number, box_label_id=box.box_label_id),
        ).expect(200)

        db_session.close()

        box = db_session.query(Box).filter_by(member_id=member.member_id).one()

        self.assertEqual(box.box_label_id, box.box_label_id)
        self.assertIsNone(box.last_nag_at)
        self.assertIsNotNone(box.last_check_at)

    def test_box_terminator_validate_status_terminate(self):
        member = self.db.create_member()
        box = self.db.create_box()

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            dict(member_number=member.member_number, box_label_id=box.box_label_id),
        ).expect(200, data__expire_date="1997-09-27", data__terminate_date="1997-11-11", data__status="terminate")

    def test_box_terminator_validate_status_expired(self):
        member = self.db.create_member()
        box = self.db.create_box()
        span = self.db.create_span(enddate=self.date(-10), type=Span.LABACCESS)

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            dict(member_number=member.member_number, box_label_id=box.box_label_id),
        ).expect(
            200,
            data__expire_date=self.date(-10 + 1).isoformat(),
            data__terminate_date=self.date(-10 + 45 + 1).isoformat(),
            data__status="expired",
        )

    def test_box_terminator_validate_status_active(self):
        member = self.db.create_member()
        box = self.db.create_box()
        span = self.db.create_span(enddate=self.date(10), type=Span.LABACCESS)

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            dict(member_number=member.member_number, box_label_id=box.box_label_id),
        ).expect(
            200,
            data__expire_date=self.date(10 + 1).isoformat(),
            data__terminate_date=self.date(10 + 45 + 1).isoformat(),
            data__status="active",
        )

    def test_box_terminator_validate_deleted_span_is_filtered(self):
        member = self.db.create_member()
        box = self.db.create_box()
        span = self.db.create_span(enddate=self.date(10), type=Span.LABACCESS, deleted_at=datetime.now(timezone.utc))

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            dict(member_number=member.member_number, box_label_id=box.box_label_id),
        ).expect(200, data__status="terminate")

    def test_box_terminator_validate_membership_span_is_filtered(self):
        member = self.db.create_member()
        box = self.db.create_box()
        span = self.db.create_span(enddate=self.date(10), type=Span.MEMBERSHIP)

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            dict(member_number=member.member_number, box_label_id=box.box_label_id),
        ).expect(200, data__status="terminate")

    def test_box_terminator_send_nag_email(self):
        member = self.db.create_member()
        box = self.db.create_box()

        self.api.post(
            "/multiaccess/box-terminator/nag",
            dict(member_number=member.member_number, box_label_id=box.box_label_id, nag_type="nag-warning"),
        ).expect(200)

        db_session.close()

        message = db_session.query(Message).filter_by(member_id=member.member_id).one()

        self.assertIn("lådan", message.body)

    def test_box_terminator_list_all_boxes(self):
        token = self.db.create_access_token()

        member1 = self.db.create_member()
        box11 = self.db.create_box()
        box12 = self.db.create_box()

        member2 = self.db.create_member()
        box21 = self.db.create_box()

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            token=token.access_token,
            json=dict(member_number=member1.member_number, box_label_id=box11.box_label_id),
        ).expect(200)

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            token=token.access_token,
            json=dict(member_number=member1.member_number, box_label_id=box12.box_label_id),
        ).expect(200)

        self.api.post(
            "/multiaccess/box-terminator/validate-box",
            token=token.access_token,
            json=dict(member_number=member2.member_number, box_label_id=box21.box_label_id),
        ).expect(200)

        data = self.api.get("/multiaccess/box-terminator/boxes", token=token.access_token).expect(200).data

        box_ids = [b["box_label_id"] for b in data]

        self.assertIn(box11.box_label_id, box_ids)
        self.assertIn(box12.box_label_id, box_ids)
        self.assertIn(box21.box_label_id, box_ids)
