from sqlalchemy import Column, Integer, String, DateTime, func, Text, Numeric, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from membership.models import Member

Base = declarative_base()


class ProductCategory(Base):
    __tablename__ = 'webshop_product_categories'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f'ProductCategory(id={self.id}, name={self.name}, display_order={self.display_order})'


class Product(Base):
    __tablename__ = 'webshop_products'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    category_id = Column(Integer, ForeignKey(ProductCategory.id), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    unit = Column(String(30))
    price = Column(Numeric(precision="15,3"), nullable=False)
    smallest_multiple = Column(Integer, nullable=False, server_default='1')
    filter = Column(String(255))
    image = Column(String(255))
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    category = relationship(ProductCategory, backref='products')
    images = relationship("ProductImage", lazy='dynamic', backref='product')
    actions = relationship("ProductAction")

    def __repr__(self):
        return f'Product(id={self.id}, name={self.name}, category_id={self.category_id}' \
               f', display_order={self.display_order})'


class ProductAction(Base):
    __tablename__ = 'webshop_product_actions'

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
    
    def __repr__(self):
        return f'ProductAction(id={self.id}, value={self.value}, action_type={self.action_type})'


class Transaction(Base):
    __tablename__ = 'webshop_transactions'

    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey(Member.member_id), nullable=False)
    amount = Column(Numeric(precision="15,2"), nullable=False)
    status = Column(Enum(PENDING, COMPLETED, FAILED), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    member = relationship(Member)
    stripe_pending = relationship("StripePending")

    def __repr__(self):
        return f'Transaction(id={self.id}, amount={self.amount}, status={self.status})'


class TransactionContent(Base):
    __tablename__ = 'webshop_transaction_contents'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    count = Column(Integer, nullable=False)
    amount = Column(Numeric(precision="15,2"), nullable=False)

    transaction = relationship(Transaction, backref='contents')
    product = relationship(Product)

    def __repr__(self):
        return f'TransactionContent(id={self.id}, count={self.count}, amount={self.amount})'

    
class TransactionAction(Base):
    __tablename__ = 'webshop_transaction_actions'

    PENDING = 'pending'
    COMPLETED = 'completed'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    content_id = Column(Integer, ForeignKey(TransactionContent.id), nullable=False)
    action_type = Column(Enum(*ProductAction.PRODUCT_ACTIONS), nullable=False)
    value = Column(Integer)
    status = Column(Enum(PENDING, COMPLETED), nullable=False)
    completed_at = Column(DateTime)

    content = relationship(TransactionContent, backref='actions')

    def __repr__(self):
        return f'TransactionAction(id={self.id}, value={self.value}, status={self.status},' \
               f' action_type={self.action_type})'


class PendingRegistration(Base):
    __tablename__ = 'webshop_pending_registrations'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)

    transaction = relationship(Transaction, backref='pending_registrations')

    def __repr__(self):
        return f'PendingRegistration(id={self.id})'
    

class ProductImage(Base):
    __tablename__ = 'webshop_product_images'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    path = Column(String(255), nullable=False)
    caption = Column(Text)
    display_order = Column(Integer, unique=True)
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f'ProductImage(id={self.id}, path={self.path})'


class StripePending(Base):
    __tablename__ = 'webshop_stripe_pending'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    stripe_token = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f'StripePending(id={self.id}, stripe_token={self.stripe_token})'
