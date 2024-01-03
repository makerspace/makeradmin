from datetime import date

from box_terminator.box_terminator import (
    EXPIRATION_TIME,
    JUDGMENT_DAY,
    Reason,
    Status,
    check_status,
    get_dates,
    get_item_from_label_id,
    get_storage_info,
)
from box_terminator.models import StorageItem, StorageMessage, StorageMessageType, StorageType
from membership.models import Member, Span
from messages.models import Message
from service.db import db_session
from test_aid.test_base import FlaskTestBase


class BoxTerminatorTest(FlaskTestBase):
    def test_get_item_from_label_id(self) -> None:
        member = self.db.create_member()
        storage_type = self.db.create_storage_type()
        item = self.db.create_storage_item(member_id=member.member_id, storage_type_id=storage_type.id)

        db_item = get_item_from_label_id(item.item_label_id)

        assert db_item.id == item.id
        assert db_item.member_id == item.member_id
        assert db_item.member_id == member.member_id
        assert db_item.storage_type_id == item.storage_type_id
        assert db_item.storage_type_id == storage_type.id
        assert db_item.item_label_id == item.item_label_id

        # Check that joins are working properly
        assert db_item.member.member_id == member.member_id
        assert db_item.member.id == member.id
        assert db_item.storage_type.id == storage_type.id
        assert db_item.storage_type.storage_type == storage_type.storage_type

    # def test_box_terminator_get_dates_box(self) -> None:
    #     member = self.db.create_member()
    #     span = self.db.create_span(enddate=self.date(-50), type=Span.LABACCESS)
    #     item = self.db.create_member_storage(MemberStorage.BOX)  # TODO
    #     dates = get_dates(item)

    #     self.assertEqual(dates["expire_lab_date"], self.date(-50))
    #     self.assertEqual(dates["terminate_lab_date"], self.date(-50 + EXPIRATION_TIME))

    #     self.assertIsNone(dates["expire_fixed_date"])
    #     self.assertIsNone(dates["terminate_fixed_date"])

    #     self.assertEqual(dates["to_termination_days"], -50 + EXPIRATION_TIME)
    #     self.assertEqual(dates["days_after_expiration"], 50)
    #     self.assertEqual(dates["pending_labaccess_days"], 0)
