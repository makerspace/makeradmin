import datetime as datetime_module
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, List, Optional, cast

import sqlalchemy
from dataclasses_json import DataClassJsonMixin, config
from service.db import db_session
from service.util import date_to_str, format_datetime
from sqlalchemy import ColumnElement, func, select

from shop.models import Product, Transaction, TransactionContent


@dataclass
class SalesByDate(DataClassJsonMixin):
    date: datetime_module.date = field(metadata=config(encoder=date_to_str))
    amount: float
    count: int


@dataclass
class SalesResponse(DataClassJsonMixin):
    id: int
    total_amount: float
    total_count: int
    by_date: List[SalesByDate]
    start_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))
    end_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))
    amount_unit: str


def product_sales(product_id: int, start: Optional[datetime], end: Optional[datetime]) -> SalesResponse:
    (amount, count) = (
        db_session.execute(
            select(
                func.coalesce(func.sum(TransactionContent.amount), 0),
                sqlalchemy.cast(func.coalesce(func.sum(TransactionContent.count), 0), sqlalchemy.Integer),
            )
            .where(TransactionContent.product_id == product_id)
            .where(Transaction.created_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
            .where(Transaction.created_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
            .where(Transaction.status == Transaction.COMPLETED)
            .join(TransactionContent.transaction)
        )
        .one()
        .t
    )

    stmt = (
        select(
            sqlalchemy.cast(Transaction.created_at, sqlalchemy.Date),
            func.sum(TransactionContent.amount),
            sqlalchemy.cast(func.sum(TransactionContent.count), sqlalchemy.Integer),
        )
        .where(TransactionContent.product_id == product_id)
        .where(Transaction.created_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .where(Transaction.created_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .where(Transaction.status == Transaction.COMPLETED)
        .group_by(sqlalchemy.cast(Transaction.created_at, sqlalchemy.Date))
        .join(TransactionContent.transaction)
    )
    by_date = [SalesByDate(row.t[0], float(row.t[1]), row.t[2]) for row in (db_session.execute(stmt).all())]

    return SalesResponse(
        id=product_id,
        total_amount=float(amount),
        total_count=count,
        by_date=by_date,
        start_time=start,
        end_time=end,
        amount_unit="SEK",
    )


def category_sales(category_id: int, start: Optional[datetime], end: Optional[datetime]) -> SalesResponse:
    (amount, count) = (
        db_session.execute(
            select(
                func.coalesce(func.sum(TransactionContent.amount), 0),
                sqlalchemy.cast(func.coalesce(func.sum(TransactionContent.count), 0), sqlalchemy.Integer),
            )
            .where(Product.category_id == category_id)
            .where(Transaction.created_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
            .where(Transaction.created_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
            .where(Transaction.status == Transaction.COMPLETED)
            .join(TransactionContent.transaction)
            .join(TransactionContent.product)
        )
        .one()
        .t
    )

    stmt = (
        select(
            sqlalchemy.cast(Transaction.created_at, sqlalchemy.Date),
            func.sum(TransactionContent.amount),
            sqlalchemy.cast(func.sum(TransactionContent.count), sqlalchemy.Integer),
        )
        .where(Product.category_id == category_id)
        .where(Transaction.created_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .where(Transaction.created_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .where(Transaction.status == Transaction.COMPLETED)
        .group_by(sqlalchemy.cast(Transaction.created_at, sqlalchemy.Date))
        .join(TransactionContent.transaction)
        .join(TransactionContent.product)
    )
    by_date = [SalesByDate(row.t[0], float(row.t[1]), row.t[2]) for row in (db_session.execute(stmt).all())]

    print(type(amount))
    print(type(count))
    return SalesResponse(
        id=category_id,
        total_amount=float(amount),
        total_count=count,
        by_date=by_date,
        start_time=start,
        end_time=end,
        amount_unit="SEK",
    )
