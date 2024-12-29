import re
from datetime import datetime
from decimal import Decimal
from logging import getLogger
from random import choice, randint, seed
from typing import Any, Dict

from basic_types.enums import AccountingEntryType, PriceLevel
from box_terminator.models import StorageItem, StorageMessage, StorageMessageType, StorageType
from faker import Faker
from membership.models import Member, Span
from messages.models import Message
from shop.models import (
    ProductAccountsCostCenters,
    ProductAction,
    Transaction,
    TransactionAccount,
    TransactionContent,
    TransactionCostCenter,
)

from test_aid.test_util import random_str

logger = getLogger("makeradmin")

DEFAULT_PASSWORD = "D9ub8$13"


def random_phone_number() -> str:
    return f"070-1{randint(int(1e6), int(9e6)):06d}"


class ObjFactory:
    """Create dicts representing entities."""

    def __init__(self, test):
        self.test = test
        self.fake = Faker("sv_SE")

        self.member = None
        self.group = None
        self.category = None
        self.product = None
        self.action = None
        self.key = None
        self.span = None
        self.message = None
        self.phone_request = None
        self.storage_message_type = None
        self.storage_message = None
        self.storage_type: None
        self.storage_item = None
        self.transaction = None
        self.transaction_content = None
        self.transaction_account = None
        self.transaction_cost_center = None
        self.product_account_cost_center = None

        seed()

    def create_member(self, **kwargs) -> Dict[str, Any]:
        firstname = self.fake.first_name()
        lastname = self.fake.last_name()
        obj = dict(
            firstname=firstname,
            lastname=lastname,
            password=None,
            address_street=self.fake.street_name(),
            address_extra="N/A",
            address_zipcode=randint(10000, 99999),
            address_city=self.fake.city(),
            address_country=self.fake.country_code(representation="alpha-2"),
            phone=random_phone_number(),
            civicregno=f"19901011{randint(1000, 9999):04d}",
            email=re.sub(
                "[^a-zA-Z0-9.!#$%&'*+\\/=?^_`{|}~\\-@\\.]",
                "_",
                f"{firstname}.{lastname}+{random_str(6)}@bmail.com".lower().replace(" ", "_"),
            ),
            price_level=PriceLevel.Normal.value,
            price_level_motivation=None,
            pending_activation=False,
        )
        obj.update(kwargs)
        self.member = obj
        return self.member

    def create_phone_request(self, **kwargs):
        obj = dict(
            phone=random_phone_number(),
            validation_code=randint(1, 999999),
            completed=False,
            timestamp=datetime.now(),
        )
        obj.update(kwargs)
        self.phone_request = obj
        return self.phone_request

    def create_group(self, **kwargs):
        obj = dict(
            name=f"group-{random_str(12)}",
            title=f"group-title-{random_str(12)}",
            description=self.fake.bs(),
        )
        obj.update(kwargs)
        self.group = obj
        return self.group

    def create_key(self, **kwargs) -> Dict[str, str]:
        obj = dict(
            tagid=str(randint(int(1e12), int(9e12))),
            description=self.fake.bs(),
        )
        obj.update(kwargs)
        self.key = obj
        return self.key

    def create_span(self, **kwargs):
        obj = dict(
            startdate=self.test.date(days=-randint(40, 60)),
            enddate=self.test.date(days=-randint(10, 30)),
            type=choice((Span.LABACCESS, Span.MEMBERSHIP, Span.SPECIAL_LABACESS)),
            creation_reason=random_str(),
        )
        obj.update(kwargs)
        self.span = obj
        return self.span

    def create_category(self, **kwargs):
        obj = dict(
            name=f"category-{random_str(12)}",
            display_order=randint(int(1e8), int(9e8)),
        )
        obj.update(kwargs)
        self.category = obj
        return self.category

    def create_product(self, **kwargs):
        category_id = kwargs.pop("category_id", None) or (self.category and self.category["id"])
        obj = dict(
            name=f"product-{random_str(12)}",
            price=100.0,
            description=self.fake.bs(),
            unit="st",
            display_order=randint(int(1e8), int(9e8)),
            smallest_multiple=1,
            filter=None,
            category_id=category_id,
            product_metadata=dict(),
        )
        obj.update(kwargs)
        self.product = obj
        return self.product

    def create_product_action(self, **kwargs):
        obj = dict(
            product_id=0,
            action_type=ProductAction.ADD_MEMBERSHIP_DAYS,
            value=365,
        )
        obj.update(**kwargs)
        self.action = obj
        return self.action

    def create_message(self, **kwargs):
        obj = dict(
            subject=random_str(),
            body=self.fake.bs(),
            recipient=self.fake.email(),
            status=Message.QUEUED,
        )
        obj.update(**kwargs)
        self.message = obj
        return self.message

    def create_transaction(self, **kwargs) -> Transaction:
        member_id = kwargs.pop("member_id", None) or (self.member and self.member["member_id"])
        obj = dict(
            status=Transaction.COMPLETED,
            amount=Decimal("100.0"),
            member_id=member_id,
        )
        obj.update(**kwargs)
        self.transaction = obj
        return self.transaction

    def create_transaction_content(self, **kwargs) -> TransactionContent:
        transaction_id = kwargs.pop("transaction_id", None) or (self.transaction and self.transaction["id"])
        product_id = kwargs.pop("product_id", None) or (self.product and self.product["id"])
        obj = dict(
            transaction_id=transaction_id,
            product_id=product_id,
            count=1,
            amount=100.0,
        )
        obj.update(**kwargs)
        self.transaction_content = obj
        return self.transaction_content

    def create_transaction_account(self, **kwargs) -> TransactionAccount:
        obj = dict(
            account=f"account-{random_str(5)}",
            description=f"desc-{random_str(12)}",
            display_order=randint(int(1e8), int(9e8)),
        )
        obj.update(kwargs)
        self.transaction_account = obj
        return self.transaction_account

    def create_transaction_cost_center(self, **kwargs) -> TransactionCostCenter:
        obj = dict(
            cost_center=f"cost-center-{random_str(5)}",
            description=f"desc-{random_str(12)}",
            display_order=randint(int(1e8), int(9e8)),
        )
        obj.update(kwargs)
        self.transaction_cost_center = obj
        return self.transaction_cost_center

    def create_product_account_cost_center(self, **kwargs) -> ProductAccountsCostCenters:
        product_id = kwargs.pop("product_id", None) or (self.product and self.product["id"])
        account_id = kwargs.pop("account_id", None)
        cost_center_id = kwargs.pop("cost_center_id", None)

        obj = dict(
            account_id=account_id,
            cost_center_id=cost_center_id,
            product_id=product_id,
            fraction=100,
            type=AccountingEntryType.CREDIT,
        )
        obj.update(**kwargs)
        self.product_account_cost_center = obj
        return self.product_account_cost_center

    def create_storage_message_type(self, **kwargs) -> StorageItem:
        obj = dict(
            message_type=f"message_type-{random_str(12)}",
            display_order=randint(int(1e8), int(9e8)),
        )
        obj.update(kwargs)
        self.storage_message_type = obj
        return self.storage_message_type

    def create_storage_message(self, **kwargs) -> StorageItem:
        member_id = kwargs.pop("member_id", None) or (self.member and self.member["id"])
        storage_message_type_id = kwargs.pop("storage_message_type_id", None) or (
            self.storage_message_type and self.storage_message_type["id"]
        )
        item_id = kwargs.pop("storage_item_id", None) or (self.storage_item and self.storage_item["id"])
        obj = dict(
            member_id=member_id,
            storage_message_type_id=storage_message_type_id,
            storage_item_id=item_id,
        )
        obj.update(kwargs)
        self.storage_message = obj
        return self.storage_message

    def create_storage_type(self, **kwargs) -> StorageItem:
        obj = dict(
            storage_type=f"storage_type-{random_str(12)}",
            display_order=randint(int(1e8), int(9e8)),
            has_fixed_end_date=False,
        )
        obj.update(kwargs)
        self.storage_type = obj
        return self.storage_type

    def create_storage_item(self, **kwargs) -> StorageItem:
        member_id = kwargs.pop("member_id", None) or (self.member and self.member["id"])
        storage_type_id = kwargs.pop("storage_type_id", None) or (self.storage_type and self.storage_type["id"])
        obj = dict(
            item_label_id=randint(int(1e8), int(9e8)),
            member_id=member_id,
            storage_type_id=storage_type_id,
        )
        obj.update(kwargs)
        self.storage_item = obj
        return self.storage_item
