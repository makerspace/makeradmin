import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import sqlalchemy
from dataclasses_json import DataClassJsonMixin
from membership.models import Member
from multiaccessy.models import PhysicalAccessEntry
from service.db import db_session
from service.logging import logger
from shop.models import Product, ProductCategory, Transaction, TransactionContent
from sqlalchemy import desc, distinct, func, select


def score_members_by_amount_purchased(
    products: Sequence[Product], start: Optional[datetime], end: Optional[datetime], limit: Optional[int] = 30
) -> List[Tuple[Member, float]]:
    product_ids = [product.id for product in products]
    stmt = (
        select(Member, func.sum(TransactionContent.amount).label("amount"))
        .where(Product.id.in_(product_ids))
        .where(Transaction.created_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .where(Transaction.created_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .order_by(func.sum(TransactionContent.amount).desc())
        .limit(limit)
        .group_by(Member.member_id)
        .join(Transaction, Member.member_id == Transaction.member_id)
        .join(TransactionContent, Transaction.id == TransactionContent.transaction_id)
        .join(TransactionContent.product)
    )
    return [(member, amount) for (member, amount) in db_session.execute(stmt)]


def days_with_visits(
    start: Optional[datetime], end: Optional[datetime], limit: Optional[int] = 30
) -> List[Tuple[Member, int]]:
    unique_days = func.count(distinct(func.DATE(PhysicalAccessEntry.invoked_at)))
    stmt = (
        select(Member, unique_days.label("days_with_visits"))
        .where(
            PhysicalAccessEntry.invoked_at >= start if start is not None else sqlalchemy.cast(True, sqlalchemy.Boolean)
        )
        .where(PhysicalAccessEntry.invoked_at < end if end is not None else sqlalchemy.cast(True, sqlalchemy.Boolean))
        .having(unique_days > 0)
        .limit(limit)
        .order_by(desc(unique_days))
        .group_by(Member.member_id)
        .join(PhysicalAccessEntry, Member.member_id == PhysicalAccessEntry.member_id)
    )
    return [(member, count) for (member, count) in db_session.execute(stmt)]


def percentiles(members: List[Tuple[Member, int]]) -> Dict[Member, Tuple[float, int]]:
    n = len(members)
    result: Dict[Member, Tuple[float, int]] = {}
    for i, (member, value) in enumerate(members):
        percentile = (i + 1) / n
        result[member] = (percentile, value)
    return result


@dataclass
class ActivityGroup:
    name: str
    scores: Dict[str, float]


@dataclass
class MemberScore(DataClassJsonMixin):
    member_id: int
    member_number: int
    firstname: str
    lastname: str | None
    activity_percentile: float
    score: float


@dataclass
class ActivityGroupStatistics(DataClassJsonMixin):
    name: str
    products: List[Tuple[int, str, float]]
    doors: List[Tuple[str, str, float]]
    member_scores: List[MemberScore]


@dataclass
class MembersOfInterestResponse(DataClassJsonMixin):
    groups: List[ActivityGroupStatistics]


def members_of_interest(start: Optional[datetime], end: Optional[datetime]) -> MembersOfInterestResponse:
    member_activity = days_with_visits(start, end, limit=None)
    member_percentiles = percentiles(member_activity)

    # TODO: This should ideally be moved to a config file
    groups = [
        ActivityGroup(
            name="General activity",
            scores={
                "opens_door:%": 1,
            },
        ),
        ActivityGroup(
            name="Laser",
            scores={
                "category:Förbrukning laser": 1,
                "product:Använding av Laserskärare": 2,
            },
        ),
        ActivityGroup(
            name="Woodworking",
            scores={
                "product:MDF%": 1,
                "product:Plywood%": 1,
                "product:Använding av Laserskärare": -5,
            },
        ),
        ActivityGroup(
            name="CNC",
            scores={
                "category:Verktyg för fräs": 1,
                "product:Aluminum": 1,
                "product:Brass": 1,
                "product:Plastic": 1,
            },
        ),
        ActivityGroup(
            name="Embroidery",
            scores={
                "product:Use of embroidery machine": 1,
            },
        ),
        ActivityGroup(
            name="Welding",
            scores={
                "product:Steel": 1,
                "category:Verktyg för svarv": -1,
                "category:Verktyg för fräs": -0.5,
            },
        ),
        ActivityGroup(
            name="Sand blasting",
            scores={
                "category:Förbrukning skärmaskin": 0.1,
                "product:Adhesive vinyl - sandblaster mask": 1,
            },
        ),
        ActivityGroup(
            name="Vinyl",
            scores={
                "category:Förbrukning skärmaskin": 1,
            },
        ),
        ActivityGroup(
            name="3D Printing",
            scores={
                "category:Förbrukning 3D-Skrivare": 1,
            },
        ),
        ActivityGroup(
            name="Large Format Printing",
            scores={
                "category:Förbrukning Storformatsskrivare": 1,
                "product:Printing- paper": 0.1,
            },
        ),
        ActivityGroup(
            name="Electronics",
            scores={
                "category:Utvecklingskort Elektronikrummet": 1,
                "opens_door:1de7a08c-b169-4967-ae02-8082e018d538": 5,
                "product:Use of embroidery machine": -10,
            },
        ),
    ]

    result: List[ActivityGroupStatistics] = []

    for group in groups:
        product_scores: Dict[Product, float] = {}
        member_scores: Dict[Member, float] = {}
        doors: List[Tuple[str, str, float]] = []

        for score_key, multiplier in group.scores.items():
            if score_key.startswith("category:"):
                score_key = score_key[len("category:") :]
                products = db_session.scalars(
                    select(Product).join(Product.category).filter(ProductCategory.name.like(score_key))
                ).all()
                for product in products:
                    product_scores[product] = multiplier
                if len(products) == 0:
                    logger.warning(
                        f"Could not find category with name like '{score_key}', or category is empty. When generating statistics for members of interest."
                    )
            elif score_key.startswith("product:"):
                score_key = score_key[len("product:") :]
                products = db_session.scalars(select(Product).filter(Product.name.like(score_key))).all()
                for product in products:
                    product_scores[product] = multiplier
                if len(products) == 0:
                    logger.warning(
                        f"Could not find product with name like '{score_key}'. When generating statistics for members of interest."
                    )
            elif score_key.startswith("opens_door:"):
                score_key = score_key[len("opens_door:") :]
                entries = db_session.execute(
                    select(Member, func.count(distinct(func.date_format(PhysicalAccessEntry.invoked_at, "%Y-%m-%d"))))
                    .join(PhysicalAccessEntry, Member.member_id == PhysicalAccessEntry.member_id)
                    .filter(PhysicalAccessEntry.accessy_asset_publication_id.like(score_key))
                    .filter(
                        PhysicalAccessEntry.invoked_at >= start
                        if start is not None
                        else sqlalchemy.cast(True, sqlalchemy.Boolean)
                    )
                    .filter(
                        PhysicalAccessEntry.invoked_at < end
                        if end is not None
                        else sqlalchemy.cast(True, sqlalchemy.Boolean)
                    )
                    .group_by(Member.member_id)
                ).t.all()
                doors.append(
                    (
                        score_key,
                        "Open any accessy door" if score_key == "%" else f"Open accessy door {score_key}",
                        multiplier,
                    )
                )
                for member, days_visited in entries:
                    member_scores[member] = member_scores.get(member, 0) + int(days_visited) * multiplier
                if len(entries) == 0:
                    logger.warning(
                        f"Could not find any members that opened the door with publication id like '{score_key}'. When generating statistics for members of interest."
                    )
            else:
                logger.error(f"Unknown score key: {score_key}")

        for product, multiplier in product_scores.items():
            for member, score in score_members_by_amount_purchased([product], start, end, limit=100):
                member_scores[member] = member_scores.get(member, 0) + int(score) * multiplier

        scores = [(score, member) for (member, score) in member_scores.items()]
        scores.sort(reverse=True, key=lambda x: x[0])
        scores = scores[:30]

        result.append(
            ActivityGroupStatistics(
                name=group.name,
                products=[(product.id, product.name, score) for product, score in product_scores.items()],
                doors=doors,
                member_scores=[
                    MemberScore(
                        member.member_id,
                        member.member_number,
                        member.firstname,
                        member.lastname,
                        member_percentiles.get(member, (1, 0))[0],
                        score,
                    )
                    for score, member in scores
                ],
            )
        )

    return MembersOfInterestResponse(groups=result)
