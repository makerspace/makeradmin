from typing import Any

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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import configure_mappers, relationship, validates

from shop.stripe_constants import MakerspaceMetadataKeys

Base = declarative_base()


class ProductCategory(Base):
    __tablename__ = "webshop_product_categories"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"ProductCategory(id={self.id}, name={self.name}, display_order={self.display_order})"


class ProductImage(Base):
    __tablename__ = "webshop_product_images"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(255), nullable=False)
    type = Column(String(64), nullable=False)
    data = Column(LargeBinary)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"ProductImage(id={self.id}, path={self.path})"


class Product(Base):
    __tablename__ = "webshop_products"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_metadata = Column(JSON, nullable=False)
    category_id = Column(Integer, ForeignKey(ProductCategory.id), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    unit = Column(String(30))
    price = Column(Numeric(precision="15,3"), nullable=False)
    smallest_multiple = Column(Integer, nullable=False, server_default="1")
    filter = Column(String(255))
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)
    show = Column(Boolean, nullable=False, server_default="1")

    category = relationship(ProductCategory, backref="products")
    actions = relationship("ProductAction")

    image_id = Column(Integer, ForeignKey(ProductImage.id), nullable=True)

    def get_metadata(self, key: MakerspaceMetadataKeys, default: Any) -> Any:
        meta = self.product_metadata
        assert isinstance(meta, dict)
        return meta.get(key.value, default)

    @validates("price")
    def validate_name(self, key, value):
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

    ADD_LABACCESS_DAYS = "add_labaccess_days"
    ADD_MEMBERSHIP_DAYS = "add_membership_days"

    PRODUCT_ACTIONS = (ADD_LABACCESS_DAYS, ADD_MEMBERSHIP_DAYS)

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    action_type = Column(Enum(*PRODUCT_ACTIONS), nullable=False)
    value = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"ProductAction(id={self.id}, value={self.value}, action_type={self.action_type})"


class Transaction(Base):
    __tablename__ = "webshop_transactions"

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey(Member.member_id), nullable=True)
    amount = Column(Numeric(precision="15,2"), nullable=False)
    status = Column(Enum(PENDING, COMPLETED, FAILED), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    member = relationship(Member)
    stripe_pending = relationship("StripePending")

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, amount={self.amount}, status={self.status}, created_at={self.created_at})"


class TransactionContent(Base):
    __tablename__ = "webshop_transaction_contents"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    count = Column(Integer, nullable=False)
    amount = Column(Numeric(precision="15,2"), nullable=False)

    transaction = relationship(Transaction, backref="contents")
    product = relationship(Product)

    def __repr__(self) -> str:
        return f"TransactionContent(id={self.id}, count={self.count}, amount={self.amount})"


class TransactionAction(Base):
    __tablename__ = "webshop_transaction_actions"

    PENDING = "pending"
    COMPLETED = "completed"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    content_id = Column(Integer, ForeignKey(TransactionContent.id), nullable=False)
    action_type = Column(Enum(*ProductAction.PRODUCT_ACTIONS), nullable=False)
    value = Column(Integer)
    status = Column(Enum(PENDING, COMPLETED), nullable=False)
    completed_at = Column(DateTime)

    content = relationship(TransactionContent, backref="actions")

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

    VALID = "valid"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    amount = Column(Numeric(precision="15,2"), nullable=False)
    validation_code = Column(String(16), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    status = Column(Enum(VALID, USED, EXPIRED, CANCELLED), nullable=False, default=VALID)
    created_at = Column(DateTime, server_default=func.now())


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

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    gift_card_id = Column(Integer, ForeignKey(GiftCard.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    product_quantity = Column(Integer, nullable=False)
    amount = Column(Numeric(precision="15,2"), nullable=False)

    gift_card = relationship(GiftCard, backref="products")
    product = relationship(Product)


class TransactionAccount(Base):
    __tablename__ = "webshop_transaction_accounts"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    account = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"TransactionAccount(id={self.id}, account={self.account}, description={self.description})"


class TransactionCostcenter(Base):
    __tablename__ = "webshop_transaction_cost_centers"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    cost_center = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"TransactionConstCenter(id={self.id}, cost_center={self.cost_center}, description={self.description})"


class ProductAccountsCostCenters(Base):
    __tablename__ = "webshop_product_accounting"

    DEBIT = "debit"
    CREDIT = "credit"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = Column(Integer, ForeignKey("webshop_products.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("webshop_transaction_accounts.id"), nullable=True)
    cost_center_id = Column(Integer, ForeignKey("webshop_transaction_cost_centers.id"), nullable=True)
    fraction = Column(Numeric(6, 3), nullable=False, server_default=("0.0"))
    type = Column(Enum(DEBIT, CREDIT), nullable=False)

    product = relationship(Product, backref="accounts_cost_centers")
    account = relationship(TransactionAccount, backref="accounts_cost_centers")
    cost_center = relationship(TransactionCostcenter, backref="accounts_cost_centers")

    def __repr__(self) -> str:
        return f"ProductAccountsCostCenters(id={self.id}, cost_center={self.cost_center}, account={self.account}, debits={self.debits}, credits={self.credits})"


class StripePending(Base):
    __tablename__ = "webshop_stripe_pending"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    stripe_token = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"StripePending(id={self.id}, stripe_token={self.stripe_token})"


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
