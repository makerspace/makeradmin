from logging import getLogger
from random import randint
from typing import Optional

from box_terminator.models import StorageItem, StorageMessage, StorageMessageType, StorageType
from core.models import AccessToken, PasswordResetToken
from core.service_users import TEST_SERVICE_USER_ID
from faker import Faker
from membership.models import Group, Key, Member, Permission, PhoneNumberChangeRequest, Span
from messages.models import Message
from service.db import db_session
from shop.models import Product, ProductAction, ProductCategory, Transaction

from test_aid.obj import ObjFactory
from test_aid.test_util import random_str

logger = getLogger("makeradmin")


class DbFactory:
    """Create entities directly in the db, uses db_session to access the db so it can be used for both remote db
    access and in memory db."""

    def __init__(self, test, obj_factory: Optional[ObjFactory] = None) -> None:
        self.test = test
        self.obj = obj_factory

        self.fake = Faker("sv_SE")

        self.access_token: Optional[AccessToken] = None
        self.member: Optional[Member] = None
        self.group: Optional[Group] = None
        self.span: Optional[Span] = None
        self.key: Optional[Key] = None
        self.permission: Optional[Permission] = None
        self.message: Optional[Message] = None
        self.category: Optional[ProductCategory] = None
        self.product: Optional[Product] = None
        self.action: Optional[ProductAction] = None
        self.password_reset_token: Optional[PasswordResetToken] = None
        self.phone_request: Optional[PhoneNumberChangeRequest] = None
        self.storage_message_type: Optional[StorageMessageType] = None
        self.storage_message: Optional[StorageMessage] = None
        self.storage_type: Optional[StorageType] = None
        self.storage_item: Optional[StorageItem] = None

    def create_access_token(self, **kwargs) -> AccessToken:
        obj = dict(
            user_id=TEST_SERVICE_USER_ID,
            access_token=random_str(),
            browser=f"a-browser-{random_str()}",
            ip=f"{randint(0, 255)}.{randint(0, 255)}.{randint(0, 255)}.{randint(0, 255)}",
            expires=self.test.datetime(days=1),
        )
        obj.update(kwargs)
        self.access_token = AccessToken(**obj)
        db_session.add(self.access_token)
        db_session.commit()
        return self.access_token

    def create_member(self, **kwargs) -> Member:
        assert self.obj is not None
        obj = self.obj.create_member(**kwargs)
        self.member = Member(**obj, member_number=self.get_member_number())
        db_session.add(self.member)
        db_session.commit()
        return self.member

    def create_phone_request(self, **kwargs) -> PhoneNumberChangeRequest:
        assert self.obj is not None
        obj = self.obj.create_phone_request(**kwargs)
        self.phone_request = PhoneNumberChangeRequest(**obj, member=self.member)
        db_session.add(self.phone_request)
        db_session.commit()
        return self.phone_request

    def create_group(self, **kwargs) -> Group:
        assert self.obj is not None
        obj = self.obj.create_group(**kwargs)
        self.group = Group(**obj)
        db_session.add(self.group)
        db_session.commit()
        return self.group

    def create_span(self, **kwargs) -> Span:
        assert self.obj is not None
        if "member" in kwargs:
            member = kwargs.pop("member")
        else:
            assert self.member is not None
            member = self.member

        obj = self.obj.create_span(**kwargs)
        self.span = Span(**obj, member=member)
        db_session.add(self.span)
        db_session.commit()
        return self.span

    def create_key(self, **kwargs) -> Key:
        assert self.obj is not None
        if "member" in kwargs:
            member = kwargs.pop("member")
        else:
            assert self.member is not None
            member = self.member

        obj = self.obj.create_key(**kwargs)
        self.key = Key(**obj, member=member)
        db_session.add(self.key)
        db_session.commit()
        return self.key

    def create_message(self, member: Optional[Member] = None, **kwargs) -> Message:
        member = member or self.member
        assert member is not None

        obj = dict(
            member=member,
            subject=random_str(),
            body=self.fake.bs(),
            recipient=member.email if member else self.fake.email(),
            status=Message.QUEUED,
        )
        obj.update(**kwargs)
        self.message = Message(**obj)
        db_session.add(self.message)
        db_session.commit()
        return self.message

    def create_permission(self, **kwargs) -> Permission:
        obj = dict(
            permission=random_str(),
        )
        obj.update(kwargs)
        self.permission = Permission(**obj)
        db_session.add(self.permission)
        db_session.commit()
        return self.permission

    def get_member_number(self) -> int:
        # Ugly but will work most of the time.
        while True:
            member_number = randint(5000, 2000000)
            sql = "SELECT 1 FROM membership_members WHERE member_number = :number"
            if db_session.execute(sql, params=dict(number=member_number)).first() is None:
                break
        return member_number

    def create_category(self, **kwargs) -> ProductCategory:
        assert self.obj is not None
        obj = self.obj.create_category(**kwargs)
        self.category = ProductCategory(**obj)
        db_session.add(self.category)
        db_session.commit()
        return self.category

    def delete_category(self, id: Optional[int] = None) -> None:
        assert self.category is not None
        category_id = id or self.category.id
        assert category_id is not None
        db_session.query(ProductCategory).filter(ProductCategory.id == category_id).delete()
        db_session.flush()

    def create_product(self, **kwargs) -> Product:
        assert self.obj is not None
        if self.category:
            kwargs.setdefault("category_id", self.category.id)

        obj = self.obj.create_product(**kwargs)

        self.product = Product(**obj)
        db_session.add(self.product)
        db_session.flush()
        return self.product

    def delete_product(self, id: Optional[int] = None) -> None:
        product_id = id
        if product_id is None:
            assert self.product is not None
            product_id = self.product.id
        assert product_id is not None
        db_session.query(ProductAction).filter(ProductAction.product_id == product_id).delete()
        db_session.query(Product).filter(Product.id == product_id).delete()
        db_session.flush()

    def create_product_action(self, **kwargs) -> ProductAction:
        assert self.obj is not None
        if self.product:
            kwargs.setdefault("product_id", self.product.id)

        obj = self.obj.create_product_action(**kwargs)
        self.action = ProductAction(**obj)
        db_session.add(self.action)
        db_session.flush()
        return self.action

    def create_password_reset_token(self, member: Optional[Member] = None, **kwargs) -> PasswordResetToken:
        member = member or self.member
        assert member is not None

        if "member_id" not in kwargs:
            kwargs["member_id"] = member.member_id
        if "token" not in kwargs:
            kwargs["token"] = (random_str(),)
        self.password_reset_token = PasswordResetToken(**kwargs)
        db_session.add(self.password_reset_token)
        db_session.commit()
        return self.password_reset_token
