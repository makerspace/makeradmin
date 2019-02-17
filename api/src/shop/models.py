from sqlalchemy import Column, Integer, String, DateTime, func, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base

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
    category_id = Column(Integer, nullable=False)  # TODO Foreign key constraint
    name = Column(String(255), nullable=False)
    description = Column(Text)
    unit = Column(String(30))
    price = Column(Numeric(precision="15,3"), nullable=False)
    smallest_multiple = Column(Integer, nullable=False, server_default=1)
    filter = Column(String(255))
    image = Column(String(255))
    display_order = Column(Integer, nullable=False, unique=True) # TODO Why unique key here but unique constratint other place?
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f'ProductCategory(id={self.id}, name={self.name})'


# webshop_actions
# webshop_product_actions
# webshop_transactions
# webshop_transaction_contents
# webshop_transaction_actions
# webshop_pending_registrations
# webshop_product_images
# webshop_product_variants
# webshop_stripe_pending
