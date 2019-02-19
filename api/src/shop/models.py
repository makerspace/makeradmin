from sqlalchemy import Column, Integer, String, DateTime, func, Text, Numeric, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base

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
        return f'ProductCategory(id={self.id}, name={self.name})'


class Product(Base):
    __tablename__ = 'webshop_products'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    category_id = Column(Integer, ForeignKey(ProductCategory.id), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    unit = Column(String(30))
    price = Column(Numeric(precision="15,3"), nullable=False)
    smallest_multiple = Column(Integer, nullable=False, server_default=1)
    filter = Column(String(255))
    image = Column(String(255))
    display_order = Column(Integer, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f'Product(id={self.id}, name={self.name})'


class Action(Base):
    __tablename__ = 'webshop_actions'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(255), nullable=False)

    def __repr__(self):
        return f'Action(id={self.id}, name={self.name})'


class ProductAction(Base):
    __tablename__ = 'webshop_product_actions'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    action_id = Column(Integer, ForeignKey(Action.id), nullable=False)
    value = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f'ProductAction(id={self.id}, value={self.value})'


PENDING = 'pending'
COMPLETED = 'completed'
FAILED = 'failed'


class Transaction(Base):
    __tablename__ = 'webshop_transactions'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, ForeignKey(Member.member_id), nullable=False)
    amount = Column(Numeric(precision="15,2"), nullable=False)
    status = Column(Enum(PENDING, COMPLETED, FAILED), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f'Transaction(id={self.id}, amount={self.amount}, status={self.status})'


class TransactionContent(Base):
    __tablename__ = 'webshop_transaction_contents'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    count = Column(Integer, nullable=False)
    amount = Column(Numeric(precision="15,2"), nullable=False)

    def __repr__(self):
        return f'TransactionContent(id={self.id}, count={self.count}, amount={self.amount})'

    
class TransactionAction(Base):
    __tablename__ = 'webshop_transaction_actions'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    content_id = Column(Integer, ForeignKey(TransactionContent.id), nullable=False)
    action_id = Column(Integer, ForeignKey(Action.id), nullable=False)
    value = Column(Integer)
    status = Column(Enum(PENDING, COMPLETED), nullable=False)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f'TransactionAction(id={self.id}, value={self.value}, status={self.status})'


class PendingRegistration(Base):
    __tablename__ = 'webshop_pending_registrations'
    
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)

    def __repr__(self):
        return f'PendingRegistration(id={self.id})'
    

class ProductImages(Base):
    __tablename__ = 'webshop_product_images'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    path = Column(String(255), nullable=False)
    caption = Column(Text)
    display_order = Column(Integer, unique=True)
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f'ProductImage(id={self.id}, path={self.path})'


class ProductVariant(Base):
    __tablename__ = 'webshop_product_variants'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(precision="15,2"), nullable=False)

    def __repr__(self):
        return f'ProductVariant(id={self.id}, name={self.name})'


class StripePending(Base):
    __tablename__ = 'webshop_stripe_pending'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    stripe_token = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f'StripePending(id={self.id}, stripe_token={self.stripe_token})'
