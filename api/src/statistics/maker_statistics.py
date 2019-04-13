from datetime import datetime
from typing import List, Tuple

from service.db import db_session
from service.logging import logger
from shop.models import Product


def spans_by_date(span_type) -> List[Tuple[str, int]]:
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
    
    dates = db_session.execute(query, {'span_type': span_type})

    dates_str = [(date.strftime("%Y-%m-%d"), count) for (date, count) in dates]

    return dates_str


def membership_by_date_statistics():
    return {
        "membership": spans_by_date("membership"),
        "labaccess": spans_by_date("labaccess"),
    }


def lasertime():
    query = db_session.execute("""
            SELECT DATE_FORMAT(webshop_transactions.created_at, "%Y-%m"), sum(webshop_transaction_contents.count)
            FROM webshop_transaction_contents
            INNER JOIN webshop_transactions
            ON webshop_transactions.id = webshop_transaction_contents.transaction_id
            WHERE webshop_transaction_contents.product_id=7 AND webshop_transactions.status='completed'
            GROUP BY DATE_FORMAT(webshop_transactions.created_at, "%Y-%m")
            """)
    
    results = [(date, int(count)) for (date, count) in query]
    logger.info(results)
    return results
