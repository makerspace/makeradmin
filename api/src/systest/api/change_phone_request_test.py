import random
from datetime import datetime, timedelta, timezone
from random import randint
from time import sleep
from unittest import skip
from unittest.mock import patch

from change_phone_request import change_phone_request, change_phone_validate
from membership.models import Member, PhoneNumberChangeRequest, normalise_phone_number
from service.db import db_session
from service.error import BadRequest, NotFound
from sqlalchemy import asc, desc
from test_aid.systest_base import ApiTest


class Test(ApiTest):
    @patch("change_phone_request.send_validation_code")
    def test_request_and_validate(self, mock_send_validation_code):
        now = datetime.now(timezone.utc)
        new_phone = "+461234567"
        member = self.db.create_member()
        old_phone = member.phone

        request_id = change_phone_request(member.member_id, new_phone)

        db_item = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.member_id == member.member_id)
            .one()
        )
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertFalse(db_item.completed)
        self.assertIsNotNone(db_item.validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        validation_code = db_item.validation_code
        mock_send_validation_code.assert_called_with(new_phone, validation_code)

        change_phone_validate(member.member_id, request_id, validation_code)

        db_item = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.member_id == member.member_id)
            .one()
        )
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertTrue(db_item.completed)
        self.assertEqual(db_item.validation_code, validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        member_db = db_session.query(Member).filter(Member.member_id == member.member_id).one()
        self.assertEqual(member_db.phone, new_phone)
        self.assertNotEqual(member_db.phone, old_phone)

    @patch("change_phone_request.send_validation_code")
    def test_request_high_num_one_member(self, mock_send_validation_code):
        member = self.db.create_member()

        for i in range(0, 10):
            r = random.randrange(int(1e8), int(9e8), 8)
            new_phone = f"+46{r}"
            change_phone_request(member.member_id, new_phone)
            mock_send_validation_code.assert_called()

        r = random.randrange(int(1e8), int(9e8), 8)
        new_phone = f"+46{r}"
        change_phone_request(member.member_id, new_phone)
        self.assertRaises(BadRequest, change_phone_request, member.member_id, new_phone)

    @patch("change_phone_request.send_validation_code")
    def test_validate_wrong_code(self, mock_send_validation_code):
        now = datetime.now(timezone.utc)
        new_phone = "+461234567"
        member = self.db.create_member()
        old_phone = member.phone

        request_id = change_phone_request(member.member_id, new_phone)

        db_item = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.member_id == member.member_id)
            .one()
        )
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertFalse(db_item.completed)
        self.assertIsNotNone(db_item.validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        validation_code = db_item.validation_code
        mock_send_validation_code.assert_called_with(new_phone, validation_code)

        self.assertRaises(NotFound, change_phone_validate, member.member_id, request_id, validation_code - 1)

        db_item = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.member_id == member.member_id)
            .one()
        )
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertFalse(db_item.completed)
        self.assertEqual(db_item.validation_code, validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        member_db = db_session.query(Member).filter(Member.member_id == member.member_id).one()
        self.assertEqual(member_db.phone, old_phone)
        self.assertNotEqual(member_db.phone, new_phone)

    @patch("change_phone_request.send_validation_code")
    def test_validate_already_used_code(self, mock_send_validation_code):
        now = datetime.now(timezone.utc)
        new_phone = "+461234567"
        member = self.db.create_member()
        old_phone = member.phone

        request_id = change_phone_request(member.member_id, new_phone)

        db_item = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.member_id == member.member_id)
            .one()
        )
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertFalse(db_item.completed)
        self.assertIsNotNone(db_item.validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        validation_code = db_item.validation_code
        mock_send_validation_code.assert_called_with(new_phone, validation_code)

        change_phone_validate(member.member_id, request_id, validation_code)
        self.assertRaises(BadRequest, change_phone_validate, member.member_id, request_id, validation_code)

        db_item = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(PhoneNumberChangeRequest.member_id == member.member_id)
            .one()
        )
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertTrue(db_item.completed)
        self.assertEqual(db_item.validation_code, validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=5))

        member_db = db_session.query(Member).filter(Member.member_id == member.member_id).one()
        self.assertEqual(member_db.phone, new_phone)
        self.assertNotEqual(member_db.phone, old_phone)

    @patch("change_phone_request.send_validation_code")
    def test_validate_mult_reqs_one_member(self, mock_send_validation_code):
        now = datetime.now(timezone.utc)
        member = self.db.create_member()
        self.db.create_phone_request(timestamp=now - timedelta(hours=1))
        self.db.create_phone_request(timestamp=now - timedelta(hours=2))

        new_phone = f"+46{randint(int(1e8), int(9e8))}"
        request_id = change_phone_request(member.member_id, new_phone)

        db_items_filter = db_session.query(PhoneNumberChangeRequest).filter(
            PhoneNumberChangeRequest.member_id == member.member_id, PhoneNumberChangeRequest.phone == new_phone
        )
        db_item = db_items_filter.order_by(desc(PhoneNumberChangeRequest.timestamp)).first()

        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertFalse(db_item.completed)
        self.assertIsNotNone(db_item.validation_code)
        self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=20))

        validation_code = db_item.validation_code
        mock_send_validation_code.assert_called_with(new_phone, validation_code)

        change_phone_validate(member.member_id, request_id, validation_code)

        db_item = (
            db_session.query(PhoneNumberChangeRequest)
            .filter(
                PhoneNumberChangeRequest.member_id == member.member_id,
                PhoneNumberChangeRequest.validation_code == validation_code,
            )
            .one()
        )
        self.assertEqual(db_item.member_id, member.member_id)
        self.assertEqual(db_item.phone, new_phone)
        self.assertTrue(db_item.completed)

        member_db = db_session.query(Member).filter(Member.member_id == member.member_id).one()
        self.assertEqual(member_db.phone, new_phone)

    @patch("change_phone_request.send_validation_code")
    def test_validate_mult_reqs_mult_members(self, mock_send_validation_code):
        now = datetime.now(timezone.utc)
        num_members = 20

        member = [None] * num_members
        for i in range(0, num_members):
            member[i] = self.db.create_member()
            self.db.create_phone_request(timestamp=now - timedelta(minutes=1))

        for i in range(0, 30):
            r = random.randrange(int(1e8), int(9e8), 8)
            new_phone = f"+46{r}"
            rand_member = member[i % num_members]
            request_id = change_phone_request(rand_member.member_id, new_phone)

            db_items_filter = db_session.query(PhoneNumberChangeRequest).filter(
                PhoneNumberChangeRequest.member_id == rand_member.member_id, PhoneNumberChangeRequest.phone == new_phone
            )
            db_item = db_items_filter.order_by(desc(PhoneNumberChangeRequest.timestamp)).first()

            self.assertEqual(db_item.member_id, rand_member.member_id)
            self.assertEqual(db_item.phone, new_phone)
            self.assertFalse(db_item.completed)
            self.assertIsNotNone(db_item.validation_code)
            self.assertTrue(abs(db_item.timestamp - now) < timedelta(seconds=20))

            validation_code = db_item.validation_code
            mock_send_validation_code.assert_called_with(new_phone, validation_code)

            change_phone_validate(rand_member.member_id, request_id, validation_code)

            db_item = (
                db_session.query(PhoneNumberChangeRequest)
                .filter(
                    PhoneNumberChangeRequest.member_id == rand_member.member_id,
                    PhoneNumberChangeRequest.validation_code == validation_code,
                )
                .one()
            )
            self.assertEqual(db_item.member_id, rand_member.member_id)
            self.assertEqual(db_item.phone, new_phone)
            self.assertTrue(db_item.completed)

            member_db = db_session.query(Member).filter(Member.member_id == rand_member.member_id).one()
            self.assertEqual(member_db.phone, new_phone)
