from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from basic_types.enums import AccountingEntryType
from membership.models import Member
from service.api_definition import BAD_VALUE
from service.error import UnprocessableEntity
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, configure_mappers, mapped_column, relationship, validates

from shop.stripe_constants import MakerspaceMetadataKeys


class Base(DeclarativeBase):
    pass


class ProductCategory(Base):
    __tablename__ = "webshop_product_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"ProductCategory(id={self.id}, name={self.name}, display_order={self.display_order})"


class ProductImage(Base):
    __tablename__ = "webshop_product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[Optional[int]] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"ProductImage(id={self.id}, name={self.name})"


class Product(Base):
    __tablename__ = "webshop_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_metadata: Mapped[Dict[any, any]] = mapped_column(JSON, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey(ProductCategory.id), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    unit: Mapped[Optional[str]] = mapped_column(String(30))
    price: Mapped[Decimal] = mapped_column(Numeric(precision="15,3"), nullable=False)
    smallest_multiple: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    filter: Mapped[Optional[str]] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    show: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    stripe_product_id: Mapped[Optional[str]] = mapped_column(String(64))

    category: Mapped[ProductCategory] = relationship(ProductCategory, backref="products", cascade_backrefs=False)
    actions: Mapped[List["ProductAction"]] = relationship("ProductAction")
    product_accounting: Mapped["ProductAccountsCostCenters"] = relationship(
        "ProductAccountsCostCenters", backref="accounts_cost_centers", cascade_backrefs=False
    )

    image_id: Mapped[int] = mapped_column(Integer, ForeignKey(ProductImage.id), nullable=True)

    def get_metadata(self, key: MakerspaceMetadataKeys, default: Any) -> Any:
        meta = self.product_metadata
        assert isinstance(meta, dict)
        return meta.get(key.value, default)

    @validates("price")
    def validate_name(self, key: str, value: Decimal) -> Decimal:
        if value < 0:
            raise UnprocessableEntity(f"Price can't be below zero.", fields=key, what=BAD_VALUE)
        return value

    def __repr__(self) -> str:
        return (
            f"Product(id={self.id}, name={self.name}, category_id={self.category_id}"
            f", display_order={self.display_order}, metadata={self.product_metadata})"
        )


class ProductAction(Base):
    __tablename__ = "webshop_product_actions"

    PRODUCT_ACTIONS = Literal["add_labaccess_days", "add_membership_days"]
    ADD_LABACCESS_DAYS: PRODUCT_ACTIONS = "add_labaccess_days"
    ADD_MEMBERSHIP_DAYS: PRODUCT_ACTIONS = "add_membership_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey(Product.id), nullable=False)
    action_type: Mapped[PRODUCT_ACTIONS] = mapped_column(Enum(ADD_LABACCESS_DAYS, ADD_MEMBERSHIP_DAYS), nullable=False)
    value: Mapped[Optional[int]]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"ProductAction(id={self.id}, value={self.value}, action_type={self.action_type})"


class Transaction(Base):
    __tablename__ = "webshop_transactions"

    STATUS = Literal["pending", "completed", "failed"]
    PENDING: STATUS = "pending"
    COMPLETED: STATUS = "completed"
    FAILED: STATUS = "failed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey(Member.member_id), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision="15,2"), nullable=False)
    status: Mapped[STATUS] = mapped_column(Enum(PENDING, COMPLETED, FAILED), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    member: Mapped[Member] = relationship(Member)
    stripe_pending: Mapped[list["StripePending"]] = relationship("StripePending")

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, amount={self.amount}, status={self.status}, created_at={self.created_at})"


class TransactionContent(Base):
    __tablename__ = "webshop_transaction_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey(Transaction.id), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey(Product.id), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision="15,2"), nullable=False)

    transaction: Mapped[Transaction] = relationship(Transaction, backref="contents", cascade_backrefs=False)
    product: Mapped[Product] = relationship(Product)

    def __repr__(self) -> str:
        return f"TransactionContent(id={self.id}, count={self.count}, amount={self.amount})"


class TransactionAction(Base):
    __tablename__ = "webshop_transaction_actions"

    STATUS = Literal["pending", "completed"]
    PENDING: STATUS = "pending"
    COMPLETED: STATUS = "completed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey(TransactionContent.id), nullable=False)
    action_type: Mapped[ProductAction.PRODUCT_ACTIONS] = mapped_column(
        Enum(ProductAction.ADD_MEMBERSHIP_DAYS, ProductAction.ADD_LABACCESS_DAYS), nullable=False
    )
    value: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[STATUS] = mapped_column(Enum(PENDING, COMPLETED), nullable=False)
    completed_at: Mapped[Optional[datetime]]

    content: Mapped[TransactionContent] = relationship(TransactionContent, backref="actions", cascade_backrefs=False)

    def __repr__(self) -> str:
        return (
            f"TransactionAction(id={self.id}, value={self.value}, status={self.status},"
            f" action_type={self.action_type})"
        )


class GiftCard(Base):
    """
    Represents a gift card in the webshop.

    Attributes:
        id (int): Unique identifier for gift card.
        amount (float): the monetary value associated with the gift card.
        validation_code (str): The unique hex code used to validate the gift card. Length is 16 characters.
        email (str): The email address associated with the gift card. Used to send the validation code to the client.
        status (enum): The status of the gift card
        created_at (datetime): the timestamp when the card was created.
    """

    __tablename__ = "webshop_gift_card"

    STATUS = Literal["valid", "used", "expired", "cancelled"]
    VALID: STATUS = "valid"
    USED: STATUS = "used"
    EXPIRED: STATUS = "expired"
    CANCELLED: STATUS = "cancelled"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision="15,2"), nullable=False)
    validation_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[STATUS] = mapped_column(Enum(VALID, USED, EXPIRED, CANCELLED), nullable=False, default=VALID)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProductGiftCardMapping(Base):
    """
    Represents the mapping between a Products and a Gift cards in the webshop.

    Attributes:
        id (int): Unique identifier for the mapping.
        gift_card_id (int): The ID of the associated gift card.
        product_id (int): The ID of the associated product.
        product_quantity (int): The quantity of the product associated with the gift card.

    Relationships:
        gift_card (GiftCard): The gift card associated with the mapping.
        product (Product): The product associated with the mapping.
    """

    __tablename__ = "webshop_product_gift_card_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    gift_card_id: Mapped[int] = mapped_column(Integer, ForeignKey(GiftCard.id), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey(Product.id), nullable=False)
    product_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision="15,2"), nullable=False)

    gift_card: Mapped[GiftCard] = relationship(GiftCard, backref="products", cascade_backrefs=False)
    product: Mapped[Product] = relationship(Product)


class TransactionAccount(Base):
    __tablename__ = "webshop_transaction_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    account: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]

    def __repr__(self) -> str:
        return f"TransactionAccount(id={self.id}, account={self.account}, description={self.description})"


class TransactionCostCenter(Base):
    __tablename__ = "webshop_transaction_cost_centers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    cost_center: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]]

    def __repr__(self) -> str:
        return f"TransactionConstCenter(id={self.id}, cost_center={self.cost_center}, description={self.description})"


class ProductAccountsCostCenters(Base):
    __tablename__ = "webshop_product_accounting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("webshop_products.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("webshop_transaction_accounts.id"), nullable=True)
    cost_center_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("webshop_transaction_cost_centers.id"), nullable=True
    )
    fraction: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=("0")
    )  # Using integer with the range 0-100 to represent fractions and avoind precision issues
    type: Mapped[str] = mapped_column(Enum(*[x.value for x in AccountingEntryType]), nullable=False)

    account: Mapped[TransactionAccount] = relationship(
        TransactionAccount, backref="accounts_cost_centers", cascade_backrefs=False
    )
    cost_center: Mapped[TransactionCostCenter] = relationship(
        TransactionCostCenter, backref="accounts_cost_centers", cascade_backrefs=False
    )

    def __repr__(self) -> str:
        return f"ProductAccountsCostCenters(id={self.id}, account_id={self.account_id}, cost_center_id={self.cost_center_id}, type={self.type}, fraction={self.fraction})"


class StripePending(Base):
    __tablename__ = "webshop_stripe_pending"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey(Transaction.id), nullable=False)
    stripe_token: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"StripePending(id={self.id}, stripe_token={self.stripe_token})"


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
