from datetime import datetime, timedelta, date
from typing import List, Tuple
import math
from membership.membership import get_membership_summaries

from service.db import db_session
from service.logging import logger
from shop.models import Product, Transaction, TransactionContent, ProductCategory
from shop.entities import product_entity, category_entity
from membership.models import Member, Span
from sqlalchemy import func
import itertools


def spans_by_date(span_type) -> List[Tuple[str, int]]:
    """Number of active spans of a given type indexed by a date string"""
    # Warning: doesn't accurately add datapoints when the number of members drops to zero
    # But since we know that Stockholm Makerspace will exist forever, this is an edge case that will never happen.
    query = """
    SELECT date, count(distinct(member_id)) AS labmembers
        FROM membership_spans as ms
        JOIN (
            (SELECT enddate AS date FROM membership_spans WHERE type = :span_type AND deleted_at IS NULL)
            UNION DISTINCT
            (SELECT DATE_ADD(enddate, INTERVAL 1 DAY) as date FROM membership_spans
               WHERE type = :span_type AND deleted_at IS NULL)
            UNION DISTINCT
            (SELECT startdate FROM membership_spans
                WHERE type = :span_type AND deleted_at IS NULL)
            UNION DISTINCT
            (SELECT DATE_SUB(startdate, INTERVAL 1 DAY) FROM membership_spans
               WHERE type = :span_type AND deleted_at IS NULL)
        ) AS dates
        ON (
            ms.startdate <= dates.date AND
            dates.date <= ms.enddate
        )
        WHERE (
            ms.type = :span_type AND
            ms.deleted_at IS NULL
        )
        GROUP BY date
        ORDER BY date;"""

    dates = db_session.execute(query, {"span_type": span_type})

    dates_str = [(date.strftime("%Y-%m-%d"), count) for (date, count) in dates]

    return dates_str


def membership_number_months(
    membership_type: str, startdate: date, enddate: date
) -> List[int]:
    """Of all members who became members before startdate, how many months have they had active lab membership between startdate and enddate. Returns a mapping of month count to member counts."""
    total_months = math.ceil((enddate - startdate).days / 30)

    spans = (
        db_session.query(Member.member_id, Span.startdate, Span.enddate)
        .join(Member.spans)
        .filter(
            Member.created_at <= startdate,
            Span.startdate < enddate,
            Span.enddate > startdate,
            Span.type == membership_type,
        )
        .all()
    )
    valid_members = (
        db_session.query(Member.member_id).filter(Member.created_at <= startdate).all()
    )
    amount_by_member = {}

    for (member_id,) in valid_members:
        amount_by_member[member_id] = timedelta(days=0)

    for (member_id, span_startdate, span_enddate) in spans:
        span_startdate: datetime = max(span_startdate, startdate)
        span_enddate: datetime = min(span_enddate, enddate)
        length = span_enddate - span_startdate
        amount_by_member[member_id] += length

    # Number of members active for exactly N months during this period
    members_active_for_months = [0] * (total_months + 1)
    for (_, member_time) in amount_by_member.items():
        days = member_time.days
        months = round(days / 30)
        if months > total_months:
            print(f"Unexpected high month count: {months}")
            months = total_months
        assert months <= total_months
        members_active_for_months[months] += 1

    return members_active_for_months


def membership_number_months2(
    membership_type: str, startdate: date, enddate: date
) -> List[int]:
    """Of all members who became members before startdate, how many months have they had active lab membership between startdate and enddate. Returns a mapping of month count to member counts."""
    total_months = math.ceil((enddate - startdate).days / 30)

    spans = (
        db_session.query(Member.member_id, Span.startdate, Span.enddate)
        .join(Member.spans)
        .filter(
            Span.startdate < enddate,
            Span.enddate > startdate,
            Span.type == membership_type,
        )
        .all()
    )
    valid_members = db_session.query(Member.member_id).all()
    amount_by_member = {}

    for (member_id,) in valid_members:
        amount_by_member[member_id] = timedelta(days=0)

    for (member_id, span_startdate, span_enddate) in spans:
        span_startdate: datetime = max(span_startdate, startdate)
        span_enddate: datetime = min(span_enddate, enddate)
        length = span_enddate - span_startdate
        amount_by_member[member_id] += length

    # Number of members active for exactly N months during this period
    members_active_for_months = [0] * (total_months + 1)
    for (_, member_time) in amount_by_member.items():
        days = member_time.days
        months = round(days / 30)
        if months > total_months:
            print(f"Unexpected high month count: {months}")
            months = total_months
        assert months <= total_months
        members_active_for_months[months] += 1

    return members_active_for_months


def membership_number_months_default():
    now = datetime.now()
    starttime = now - timedelta(days=30 * 12)
    return {
        "membership": membership_number_months(
            "membership", starttime.date(), now.date()
        ),
        "labaccess": membership_number_months(
            "labaccess", starttime.date(), now.date()
        ),
    }


def membership_number_months2_default():
    now = datetime.now()
    starttime = now - timedelta(days=30 * 12)
    return {
        "membership": membership_number_months2(
            "membership", starttime.date(), now.date()
        ),
        "labaccess": membership_number_months2(
            "labaccess", starttime.date(), now.date()
        ),
    }


def membership_by_date_statistics():
    return {
        "membership": spans_by_date("membership"),
        "labaccess": spans_by_date("labaccess"),
    }


def lasertime():
    query = db_session.execute(
        """
            SELECT DATE_FORMAT(webshop_transactions.created_at, "%Y-%m"), sum(webshop_transaction_contents.count)
            FROM webshop_transaction_contents
            INNER JOIN webshop_transactions
            ON webshop_transactions.id = webshop_transaction_contents.transaction_id
            WHERE webshop_transaction_contents.product_id=7 AND webshop_transactions.status='completed'
            GROUP BY DATE_FORMAT(webshop_transactions.created_at, "%Y-%m")
            """
    )

    results = [(date, int(count)) for (date, count) in query]
    logger.info(results)
    return results


def shop_statistics():
    # Converts a list of rows of IDs and values to a map from id to value
    def mapify(rows):
        return {r[0]: r[1] for r in rows}

    date_lower_limit = datetime.now() - timedelta(days=365)
    sales_by_product = mapify(
        db_session.query(
            TransactionContent.product_id, func.sum(TransactionContent.amount)
        )
        .join(TransactionContent.transaction)
        .filter(Transaction.created_at > date_lower_limit)
        .filter(Transaction.status == Transaction.COMPLETED)
        .group_by(TransactionContent.product_id)
        .all()
    )
    sales_by_category = mapify(
        db_session.query(Product.category_id, func.sum(TransactionContent.amount))
        .join(TransactionContent.product)
        .join(TransactionContent.transaction)
        .filter(Transaction.created_at > date_lower_limit)
        .filter(Transaction.status == Transaction.COMPLETED)
        .group_by(Product.category_id)
        .all()
    )

    product_ids = sales_by_product.keys()
    products = (
        db_session.query(Product)
        .filter((Product.deleted_at == None) | (Product.id.in_(product_ids)))
        .all()
    )
    products_json = list(map(product_entity.to_obj, list(products)))

    category_ids = sales_by_category.keys()
    categories = (
        db_session.query(ProductCategory)
        .filter(
            (ProductCategory.deleted_at == None)
            | (ProductCategory.id.in_(category_ids))
        )
        .all()
    )
    categories_json = list(map(category_entity.to_obj, list(categories)))

    return {
        "revenue_by_product_last_12_months": [
            {"product_id": r.id, "amount": float(sales_by_product.get(r.id, 0))}
            for r in products
        ],
        "revenue_by_category_last_12_months": [
            {"category_id": r.id, "amount": float(sales_by_category.get(r.id, 0))}
            for r in categories
        ],
        "products": products_json,
        "categories": categories_json,
    }


def retention_graph(startdate: date, enddate: date):
    lab_spans = (
        db_session.query(Member.member_id, Span.startdate, Span.enddate)
        .join(Member.spans)
        .filter(
            Span.startdate < enddate,
            Span.enddate > startdate,
            Span.type == Span.LABACCESS,
        )
        .order_by(Member.member_id)
        .all()
    )
    membership_spans = (
        db_session.query(Member.member_id, Span.startdate, Span.enddate)
        .join(Member.spans)
        .filter(
            Span.startdate < enddate,
            Span.enddate > startdate,
            Span.type == Span.MEMBERSHIP,
        )
        .order_by(Member.member_id)
        .all()
    )

    spans_by_member = itertools.groupby(lab_spans, key=lambda x: x[0])
    spans_by_member = [(x[0], list(x[1])) for x in spans_by_member]

    membership_spans_by_member = {
        x[0]: list(x[1])
        for x in itertools.groupby(membership_spans, key=lambda x: x[0])
    }
    members = {m.member_id: m for m in db_session.query(Member).all()}

    summaries = get_membership_summaries([x[0] for x in spans_by_member])
    assert len(summaries) == len(spans_by_member)

    nodes = {}
    links = {}

    def add_node(key: str) -> int:
        if key not in nodes:
            name = key
            if name.startswith("END"):
                name = "Inactive"

            nodes[key] = {
                "id": len(nodes),
                "name": name,
            }

        return nodes[key]["id"]

    def connect(a, b, pause: bool) -> str:
        if a is None:
            return b

        ai = add_node(a)
        bi = add_node(b)
        key = (ai, bi, pause)
        if key not in links:
            links[key] = {
                "source": ai,
                "target": bi,
                "value": 0,
                "pause": pause,
            }

        links[key]["value"] += 1
        return b

    for ((member_id, spans), summary) in zip(spans_by_member, summaries):
        member = members[member_id]
        if member_id not in membership_spans_by_member:
            print(
                f"Member {member.member_number} has {len(spans)} labaccess spans but no membership spans"
            )
            continue
        mspans = membership_spans_by_member[member_id]
        last = None

        if len(mspans) > 0:
            last = connect(last, "1st year membership", False)
        if member.labaccess_agreement_at is None:
            last = connect(last, "never signed agreement", False)
            continue

        monthId = 1
        lastEnd = None
        hadPause = False
        for span in spans:
            (_, start, end) = span
            if lastEnd is not None and (start - lastEnd).days > 7:
                hadPause = True
            months = round((end - start).days / 30)
            if months <= 0:
                continue
            for _ in range(months):
                if monthId <= 3 or monthId == 6 or monthId == 12 or monthId == 24:
                    # if monthId <= 12:
                    last = connect(last, f"{monthId}M labaccess", hadPause)
                    hadPause = False
                monthId += 1

            lastEnd = end

        if summary.labaccess_active:
            last = connect(last, "active", False)
        else:
            last = connect(last, "END " + str(last), False)

    all_links = list(links.values())
    all_nodes = list(nodes.values())

    return {
        "nodes": all_nodes,
        "links": all_links,
    }
