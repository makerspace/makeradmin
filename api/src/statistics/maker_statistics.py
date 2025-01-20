import itertools
import math
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, cast

from dataclasses_json import DataClassJsonMixin, config
from membership.membership import get_members_and_membership, get_membership_summaries
from membership.models import Member, Span
from quiz.models import QuizAnswer, QuizQuestion, QuizQuestionOption
from service.db import db_session
from service.logging import logger
from service.util import format_datetime
from shop.entities import category_entity, product_entity
from shop.models import Product, ProductCategory, Transaction, TransactionContent
from sqlalchemy import ColumnElement, Date, func, select, text


def spans_by_date(span_type: str) -> List[Tuple[str, int]]:
    """Number of active spans of a given type indexed by a date string"""
    spans = db_session.query(Span).filter(Span.type == span_type, Span.deleted_at == None).all()

    events = []
    for span in spans:
        # Make sure we calculate the correct number of members on the day before the span starts
        events.append((span.startdate - timedelta(days=1), 0, span.member_id))
        events.append((span.startdate, 1, span.member_id))
        events.append((span.enddate, 0, span.member_id))
        # enddate is inclusive, so membership is lost on the day after enddate
        events.append((span.enddate + timedelta(days=1), -1, span.member_id))

    # Note: The order of the events within a single day does not matter.
    # The result will be calculated after all events in a day have been processed.
    events.sort(key=lambda x: x[0])

    counter = 0
    active_members: Dict[int, int] = dict()
    result: List[Tuple[date, int]] = []
    if len(events) == 0:
        return []

    current_date = events[0][0]
    for d, delta, member_id in events:
        if current_date < d:
            result.append((current_date, counter))
            current_date = d

        # Need to handle overlapping spans, to avoid double counting members
        new_count = active_members.get(member_id, 0) + delta
        active_members[member_id] = new_count
        if delta == 1 and new_count == 1:
            counter += 1
        elif delta == -1 and new_count == 0:
            counter -= 1

    result.append((current_date, counter))

    return [(date.strftime("%Y-%m-%d"), count) for (date, count) in result]


def membership_number_months(membership_type: str, startdate: date, enddate: date) -> List[int]:
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
    valid_members = db_session.query(Member.member_id).filter(Member.created_at <= startdate).all()
    amount_by_member = {}

    for (member_id,) in valid_members:
        amount_by_member[member_id] = timedelta(days=0)

    for member_id, span_startdate, span_enddate in spans:
        span_startdate: datetime = max(span_startdate, startdate)
        span_enddate: datetime = min(span_enddate, enddate)
        length = span_enddate - span_startdate
        amount_by_member[member_id] += length

    # Number of members active for exactly N months during this period
    members_active_for_months = [0] * (total_months + 1)
    for _, member_time in amount_by_member.items():
        days = member_time.days
        months = round(days / 30)
        if months > total_months:
            print(f"Unexpected high month count: {months}")
            months = total_months
        assert months <= total_months
        members_active_for_months[months] += 1

    return members_active_for_months


def membership_number_months2(membership_type: str, startdate: date, enddate: date) -> List[int]:
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

    for member_id, span_startdate, span_enddate in spans:
        span_startdate: datetime = max(span_startdate, startdate)
        span_enddate: datetime = min(span_enddate, enddate)
        length = span_enddate - span_startdate
        amount_by_member[member_id] += length

    # Number of members active for exactly N months during this period
    members_active_for_months = [0] * (total_months + 1)
    for _, member_time in amount_by_member.items():
        days = member_time.days
        months = round(days / 30)
        if months > total_months:
            print(f"Unexpected high month count: {months}")
            months = total_months
        assert months <= total_months
        members_active_for_months[months] += 1

    return members_active_for_months


def membership_number_months_default():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    starttime = now - timedelta(days=30 * 12)
    return {
        "membership": membership_number_months("membership", starttime.date(), now.date()),
        "labaccess": membership_number_months("labaccess", starttime.date(), now.date()),
    }


def membership_number_months2_default():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    starttime = now - timedelta(days=30 * 12)
    return {
        "membership": membership_number_months2("membership", starttime.date(), now.date()),
        "labaccess": membership_number_months2("labaccess", starttime.date(), now.date()),
    }


def membership_by_date_statistics():
    return {
        "membership": spans_by_date("membership"),
        "labaccess": spans_by_date("labaccess"),
    }


def lasertime() -> List[Tuple[str, int]]:
    query = db_session.execute(
        text(
            """
            SELECT DATE_FORMAT(webshop_transactions.created_at, "%Y-%m"), sum(webshop_transaction_contents.count)
            FROM webshop_transaction_contents
            INNER JOIN webshop_transactions
            ON webshop_transactions.id = webshop_transaction_contents.transaction_id
            WHERE webshop_transaction_contents.product_id=7 AND webshop_transactions.status='completed'
            GROUP BY DATE_FORMAT(webshop_transactions.created_at, "%Y-%m")
            """
        )
    )

    results = [(date, int(count)) for (date, count) in query]
    return results


@dataclass
class ProductRevenue:
    product_id: int
    amount: float


@dataclass
class CategoryRevenue:
    category_id: int
    amount: float


@dataclass
class SubscriptionSplit:
    active_members: int
    has_membership_sub: int
    has_makerspace_access_sub: int
    has_both_subs: int


@dataclass
class ShopStatistics:
    revenue_by_product_last_12_months: List[ProductRevenue]
    revenue_by_category_last_12_months: List[CategoryRevenue]
    products: List[Any]
    categories: List[Any]
    subscription_split: SubscriptionSplit


def shop_statistics() -> ShopStatistics:
    # Converts a list of rows of IDs and values to a map from id to value
    def mapify(rows: List[Tuple[Any, Any]]) -> Dict[Any, Any]:
        return {r[0]: r[1] for r in rows}

    date_lower_limit = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=365)

    sales_by_product: Dict[int, float] = mapify(
        db_session.query(TransactionContent.product_id, func.sum(TransactionContent.amount))
        .join(TransactionContent.transaction)
        .filter(Transaction.created_at > date_lower_limit)
        .filter(Transaction.status == Transaction.COMPLETED)
        .group_by(TransactionContent.product_id)
        .all()
    )

    sales_by_category: Dict[int, float] = mapify(
        db_session.query(Product.category_id, func.sum(TransactionContent.amount))
        .join(TransactionContent.product)
        .join(TransactionContent.transaction)
        .filter(Transaction.created_at > date_lower_limit)
        .filter(Transaction.status == Transaction.COMPLETED)
        .group_by(Product.category_id)
        .all()
    )

    product_ids = sales_by_product.keys()
    products = db_session.query(Product).filter((Product.deleted_at == None) | (Product.id.in_(product_ids))).all()
    products_json = list(map(product_entity.to_obj, list(products)))

    category_ids = sales_by_category.keys()
    categories = (
        db_session.query(ProductCategory)
        .filter((ProductCategory.deleted_at == None) | (ProductCategory.id.in_(category_ids)))
        .all()
    )
    categories_json = list(map(category_entity.to_obj, list(categories)))

    members, memberships = get_members_and_membership()

    has_membership_sub: int = 0
    has_makerspace_access_sub: int = 0
    has_both_subs: int = 0
    total_active_members: int = 0
    for member, membership in zip(members, memberships):
        # Check if labaccess is active
        if membership.labaccess_active:
            total_active_members += 1

            if member.stripe_membership_subscription_id is not None:
                has_membership_sub += 1
            if member.stripe_labaccess_subscription_id is not None:
                has_makerspace_access_sub += 1

            if (
                member.stripe_membership_subscription_id is not None
                and member.stripe_labaccess_subscription_id is not None
            ):
                has_both_subs += 1

    return ShopStatistics(
        revenue_by_product_last_12_months=[
            ProductRevenue(product_id=r.id, amount=float(sales_by_product.get(r.id, 0))) for r in products
        ],
        revenue_by_category_last_12_months=[
            CategoryRevenue(category_id=r.id, amount=float(sales_by_category.get(r.id, 0))) for r in categories
        ],
        products=products_json,
        categories=categories_json,
        subscription_split=SubscriptionSplit(
            active_members=total_active_members,
            has_membership_sub=has_membership_sub,
            has_makerspace_access_sub=has_makerspace_access_sub,
            has_both_subs=has_both_subs,
        ),
    )


@dataclass
class RetentionGraph:
    nodes: List[Any]
    links: List[Any]


@dataclass
class RetentionNode:
    id: int
    name: str


@dataclass
class RetentionLink:
    source: int
    target: int
    value: int
    pause: bool


def retention_graph(startdate: date, enddate: date) -> RetentionGraph:
    hard_start_date = date(2016, 1, 1)
    lab_spans: List[Tuple[int, datetime, datetime]] = (
        db_session.query(Member.member_id, Span.startdate, Span.enddate)
        .join(Member.spans)
        .filter(
            Span.startdate < enddate,
            Span.enddate > hard_start_date,
            Span.type == Span.LABACCESS,
        )
        .order_by(Member.member_id, Span.enddate)
        .all()
    )
    membership_spans: List[Tuple[int, datetime, datetime]] = (
        db_session.query(Member.member_id, Span.startdate, Span.enddate)
        .join(Member.spans)
        .filter(
            Span.startdate < enddate,
            Span.enddate > hard_start_date,
            Span.type == Span.MEMBERSHIP,
        )
        .order_by(Member.member_id, Span.enddate)
        .all()
    )

    members = {m.member_id: m for m in db_session.query(Member).all()}

    spans_by_member_groups = itertools.groupby(lab_spans, key=lambda x: x[0])
    spans_by_member = [(x[0], list(x[1])) for x in spans_by_member_groups]
    has_any_spans = set([x[0] for x in spans_by_member])

    for member_id in members.keys():
        if member_id not in has_any_spans:
            spans_by_member.append((member_id, []))

    membership_spans_by_member = {x[0]: list(x[1]) for x in itertools.groupby(membership_spans, key=lambda x: x[0])}

    summaries = get_membership_summaries([x[0] for x in spans_by_member])
    assert len(summaries) == len(spans_by_member)

    nodes: Dict[str, RetentionNode] = {}
    links: Dict[Tuple[int, int, bool], RetentionLink] = {}

    def add_node(key: str) -> int:
        if key not in nodes:
            name = key
            if name.startswith("END"):
                name = "Inactive"

            nodes[key] = RetentionNode(
                id=len(nodes),
                name=name,
            )

        return nodes[key].id

    def connect(a: Optional[str], b: str, pause: bool) -> str:
        if a is None:
            return b

        ai = add_node(a)
        bi = add_node(b)
        key = (ai, bi, pause)
        if key not in links:
            links[key] = RetentionLink(
                source=ai,
                target=bi,
                value=0,
                pause=pause,
            )

        links[key].value += 1
        return b

    for (member_id, spans), summary in zip(spans_by_member, summaries):
        member = members[member_id]
        if member_id not in membership_spans_by_member:
            if len(spans) > 0:
                print(f"Member {member.member_number} has {len(spans)} labaccess spans but no membership spans")
            continue
        mspans = membership_spans_by_member[member_id]
        last = None

        last_activity = mspans[-1][2] if len(mspans) > 0 else (spans[-1][2] if len(spans) > 0 else None)
        if last_activity is not None and last_activity < startdate:
            last = connect(last, f"inactive before {startdate}", False)
            last = connect(last, f"END {startdate}", False)
            continue

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

    return RetentionGraph(nodes=all_nodes, links=all_links)


@dataclass
class MemberAttributes:
    gender: Literal["male", "female", "other", "unknown"]
    birth_year: int
    language: Literal["prefers_swedish", "prefers_english", "knows_only_english"]


@dataclass
class RetentionMember(DataClassJsonMixin):
    member_id: int
    active_months: List[bool]
    attributes: Dict[str, str | None]


@dataclass
class RetentionTable(DataClassJsonMixin):
    members: List[RetentionMember]
    start_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))
    end_time: Optional[datetime] = field(metadata=config(encoder=format_datetime))


@dataclass
class QuizQuestionMapping:
    id: str
    question_name: str
    options: Dict[str, str]


INCLUDE: ColumnElement[bool] = cast(ColumnElement[bool], cast(Any, True))


def retention_table(start: Optional[datetime], end: Optional[datetime], spantype: Span.ACCESS_TYPE) -> RetentionTable:
    spans: Sequence[Tuple[int, date, date]] = (
        db_session.execute(
            select(Member.member_id, Span.startdate, Span.enddate)
            .join(Member.spans)
            .filter(Span.type == spantype)
            .filter(Member.labaccess_agreement_at > start if start is not None else INCLUDE)
            .filter(Member.labaccess_agreement_at <= end if end is not None else INCLUDE)
            .filter(Member.labaccess_agreement_at != None)
            .order_by(Member.member_id, Span.startdate)
        )
        .tuples()
        .all()
    )

    members = {
        m.member_id: m
        for m in db_session.query(Member)
        .filter(Member.labaccess_agreement_at > start if start is not None else INCLUDE)
        .filter(Member.labaccess_agreement_at <= end if end is not None else INCLUDE)
        .filter(Member.labaccess_agreement_at != None)
        .all()
    }

    spans_by_member_groups = itertools.groupby(spans, key=lambda x: x[0])
    spans_by_member = [(x[0], list(x[1])) for x in spans_by_member_groups]
    has_any_spans = set([x[0] for x in spans_by_member])

    for member_id in members.keys():
        if member_id not in has_any_spans:
            spans_by_member.append((member_id, []))

    summaries = get_membership_summaries([x[0] for x in spans_by_member])
    assert len(summaries) == len(spans_by_member)

    interesting_questions: List[QuizQuestionMapping] = [
        QuizQuestionMapping(
            id="gender",
            question_name="What gender are you?",
            options={
                "Man": "man",
                "Woman": "woman",
                "Other": "other",
            },
        ),
        QuizQuestionMapping(
            id="language",
            question_name="Which languages do you prefer?",
            options={
                "I prefer Swedish. I understand English as well.": "prefers_swedish_knows_english",
                "I prefer Swedish. I don't understand English well. (Sorry. This quiz must be hard for you)": "knows_only_swedish",
                "I prefer English. I understand Swedish as well.": "prefers_english_knows_swedish",
                "I prefer English. I don't understand Swedish well.": "knows_only_english",
            },
        ),
    ]

    members_to_quiz_answers: Dict[int, Dict[str, str]] = {}

    for q in interesting_questions:
        question = db_session.scalar(select(QuizQuestion).where(QuizQuestion.question == q.question_name))
        if question is None:
            logger.warning(f"Question '{q.question_name}' not found when generating statistics")
            continue

        for member_id, answer in db_session.execute(
            select(Member.member_id, QuizQuestionOption.description)
            .join(QuizAnswer, QuizAnswer.member_id == Member.member_id)
            .join(QuizQuestionOption, QuizAnswer.option_id == QuizQuestionOption.id)
            .filter(QuizAnswer.question_id == question.id)
            .order_by(QuizAnswer.created_at.asc())
        ).t:
            mapped_answer = q.options.get(answer, None)
            if mapped_answer is not None:
                members_to_quiz_answers.setdefault(member_id, {})[q.id] = mapped_answer

    result: List[RetentionMember] = []
    current_year = datetime.now().year

    MONTH_LIMIT = 12 * 5
    for (member_id, spans), summary in zip(spans_by_member, summaries):
        member = members.get(member_id, None)
        if member is None:
            continue

        assert member.labaccess_agreement_at is not None

        # Spans may start before the before the agreement was signed.
        # This is the case for some old members that were migrated.
        start_date = (
            min(member.labaccess_agreement_at.date(), spans[0][1])
            if len(spans) > 0
            else member.labaccess_agreement_at.date()
        )

        active_months = [False for _ in range(MONTH_LIMIT)]
        last_month = 0
        for span in spans:
            (_, span_start, span_end) = span
            start_month = round((span_start - start_date).days / 30)
            end_month = round((span_end - start_date).days / 30)
            assert end_month >= 0 and start_month >= 0
            start_month = max(0, min(start_month - 1, len(active_months) - 1))
            end_month = max(0, min(end_month, len(active_months) - 1))
            last_month = max(last_month, end_month)
            for i in range(start_month, end_month):
                active_months[i] = True

        active_months = active_months[:last_month]

        attributes = {q.id: members_to_quiz_answers.get(member_id, {}).get(q.id, None) for q in interesting_questions}

        age_group: str | None = None
        if member.civicregno is not None:
            civicregno = member.civicregno.replace("-", "").replace(" ", "").replace("_", "")
            if len(civicregno) == 10:
                civicregno = "19" + civicregno
            if len(civicregno) == 12 and civicregno.isdecimal():
                # See https://sv.wikipedia.org/wiki/Personnummer_i_Sverige
                gender = "woman" if int(civicregno[10]) % 2 == 0 else "man"

                # If the member has answered the quiz, we trust that answer more than the personnummer
                if attributes["gender"] is None:
                    attributes["gender"] = gender

                try:
                    birth_year = int(member.civicregno.strip()[0:4])
                    if birth_year > 1930 and birth_year < current_year:
                        rounded_age = ((current_year - birth_year) // 10) * 10
                        age_group = f"{rounded_age}-{rounded_age + 9}"
                except ValueError:
                    pass

        attributes["age_group"] = age_group
        result.append(
            RetentionMember(
                member_id=member_id,
                active_months=active_months,
                attributes=attributes,
            )
        )

    return RetentionTable(
        members=result,
        start_time=start,
        end_time=end,
    )
