import math
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import getLogger
from random import random
from typing import Callable, Optional, Sequence, Tuple

from membership.models import Group, Member, member_group
from multiaccessy.models import PhysicalAccessEntry
from redis_cache import redis_connection
from serde import serde
from serde.json import from_json, to_json
from service.config import config, get_api_url, get_mysql_config
from service.db import create_mysql_engine, db_session
from shop.models import Product, Transaction, TransactionContent
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.models.blocks import (
    ActionsBlock,
    Block,
    ButtonElement,
    MarkdownTextObject,
    Option,
    PlainTextObject,
    SectionBlock,
    StaticSelectElement,
)
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import sessionmaker

from tasks import trello
from tasks.models import TaskDelegationLog, TaskDelegationLogLabel

logger = getLogger("task-delegator")

REDIS_LAST_ID_KEY = "task_delegator_last_id"

# Delay assigning tasks until a short while after the member opens the first door of the makerspace.
# This is to allow time to open other doors, which can provide hints of what areas of the space they are visiting,
# and as such, what tasks would be most relevant to assign.
ASSIGNMENT_DELAY_AFTER_START_OF_VISIT = timedelta(minutes=3)


@serde
class SlackInteractionAction:
    action_id: str
    value: str


@serde
class SlackMessage:
    ts: str


@serde
class SlackInteraction:
    action: SlackInteractionAction
    user: str
    message: SlackMessage
    trigger_id: str
    channel: str


def member_recently_received_task(member_id: int, days: int = 3) -> bool:
    since = datetime.now() - timedelta(days=days)
    c = db_session.execute(
        select(func.count()).where(TaskDelegationLog.member_id == member_id, TaskDelegationLog.created_at >= since)
    ).scalar_one()
    return c > 0


@serde
class MemberTaskInfo:
    member_id: int
    total_completed_tasks: int
    completed_tasks_by_label: dict[str, int]
    doors_opened_this_visit: set[str]
    unique_months_visited: int
    unique_days_visited: int
    groups: set[str]
    last_assigned_task: Optional[datetime]
    last_completed_task: Optional[datetime]
    purchased_product_count_by_name: dict[str, int]

    def is_in_group(self, group_name: str) -> bool:
        return group_name in self.groups

    def has_opened_door(self, door_uuid: str) -> bool:
        return door_uuid in self.doors_opened_this_visit

    def completed_tasks_with_label(self, label: str) -> int:
        return self.completed_tasks_by_label.get(label, 0)

    def purchased_product_count(self, product_name: str) -> int:
        return self.purchased_product_count_by_name.get(product_name, 0)

    @staticmethod
    def from_member(member_id: int, now: datetime) -> "MemberTaskInfo":
        member = db_session.get(Member, member_id)
        if not member:
            raise ValueError(f"Member {member_id} not found")

        total_completed_tasks = (
            db_session.execute(
                select(func.count())
                .select_from(TaskDelegationLog)
                .where(
                    TaskDelegationLog.member_id == member_id,
                    TaskDelegationLog.action == "completed",
                    TaskDelegationLog.created_at <= now,
                )
            ).scalar_one()
            or 0
        )

        completed_tasks_by_label = {}
        purchased_rows = (
            db_session.execute(
                select(TaskDelegationLogLabel.label, func.count())
                .select_from(TaskDelegationLog)
                .where(
                    TaskDelegationLog.member_id == member_id,
                    TaskDelegationLog.action == "completed",
                    TaskDelegationLog.created_at <= now,
                )
                .join(TaskDelegationLogLabel, TaskDelegationLog.id == TaskDelegationLogLabel.log_id)
                .group_by(TaskDelegationLogLabel.label)
            )
            .tuples()
            .all()
        )
        for label, count in purchased_rows:
            completed_tasks_by_label[label] = count

        groups = set(
            db_session.execute(
                select(Group.name).join(Member.groups).where(Member.member_id == member_id, Group.deleted_at == None)
            ).scalars()
        )

        doors_opened_this_visit = set(
            db_session.execute(
                select(distinct(PhysicalAccessEntry.accessy_asset_publication_id)).where(
                    PhysicalAccessEntry.member_id == member_id,
                    PhysicalAccessEntry.created_at >= now - timedelta(hours=2),
                    PhysicalAccessEntry.created_at <= now,
                )
            ).scalars()
        )

        unique_months_visited = (
            db_session.execute(
                select(func.count(distinct(func.date_format(PhysicalAccessEntry.created_at, "%Y-%m")))).where(
                    PhysicalAccessEntry.member_id == member_id,
                )
            ).scalar_one()
            or 0
        )

        unique_days_visited = (
            db_session.execute(
                select(func.count(distinct(func.date_format(PhysicalAccessEntry.created_at, "%Y-%m-%d")))).where(
                    PhysicalAccessEntry.member_id == member_id,
                )
            ).scalar_one()
            or 0
        )

        last_completed_task = db_session.execute(
            select(TaskDelegationLog.created_at)
            .where(
                TaskDelegationLog.member_id == member_id,
                TaskDelegationLog.action == "completed",
            )
            .order_by(TaskDelegationLog.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        last_assigned_task = db_session.execute(
            select(TaskDelegationLog.created_at)
            .where(
                TaskDelegationLog.member_id == member_id,
                TaskDelegationLog.action == "assigned",
            )
            .order_by(TaskDelegationLog.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        purchased_product_time_cutoff = now - timedelta(days=365)
        purchased_product_count_by_name = {}

        purchased_rows = (
            db_session.execute(
                select(Product.name, func.sum(TransactionContent.count))
                .select_from(Transaction)
                .join(TransactionContent, Transaction.id == TransactionContent.transaction_id)
                .join(TransactionContent.product)
                .where(
                    Transaction.member_id == member_id,
                    Transaction.status == Transaction.Status.completed,
                    Transaction.created_at <= now,
                    Transaction.created_at >= purchased_product_time_cutoff,
                )
                .group_by(Product.id)
            )
            .tuples()
            .all()
        )

        for product_name, count in purchased_rows:
            purchased_product_count_by_name[product_name] = int(count)

        return MemberTaskInfo(
            member_id=member.member_id,
            total_completed_tasks=total_completed_tasks,
            completed_tasks_by_label=completed_tasks_by_label,
            doors_opened_this_visit=doors_opened_this_visit,
            unique_months_visited=unique_months_visited,
            unique_days_visited=unique_days_visited,
            groups=groups,
            last_completed_task=last_completed_task,
            last_assigned_task=last_assigned_task,
            purchased_product_count_by_name=purchased_product_count_by_name,
        )


@dataclass
class TaskContext:
    member: MemberTaskInfo
    time: datetime

    @staticmethod
    def from_cache(member_id: int, now: datetime) -> "TaskContext":
        cache_key = f"member_task_info:{member_id}"
        cached = redis_connection.get(cache_key)
        if cached:
            info = from_json(MemberTaskInfo, cached)
        else:
            info = MemberTaskInfo.from_member(member_id, now)

            # This data should be immutable, as it represents a state at a given time in the past.
            # But we let it expire after some time anyway, to avoid potential issues and to get rid of unused data after a while.
            redis_connection.setex(cache_key, timedelta(days=60), to_json(info))
        return TaskContext(member=info, time=now)


@serde
class HMTime:
    h: int
    m: int


@serde
class DateDict:
    m: int
    d: int


@serde
class RecurrancePluginDataInner:
    id: str
    idCard: str
    idTargetList: str
    idTargetBoard: str
    idMember: str
    interval: int
    position: str
    time: HMTime
    period: str
    tz: str
    nextRecurrence: int  # epoch ms
    days: Optional[list[int]] = None
    dates: Optional[list[DateDict]] = None
    weekdays: Optional[list[int]] = None


# '{"recurrence":{"idCard":"6909f5bbc09c21879a0647a6","idTargetList":"6909e8297317fbe98296a733","idTargetBoard":"6909e825b9fd3246beb1b1fc","idMember":"4e9736610a46d400000116e2","interval":1,"position":"bottom","time":{"h":17,"m":33},"period":"yearly","tz":"Europe/Stockholm","nextRecurrence":1793810027000,"dates":[{"m":10,"d":4}],"id":"690a2b27f9fde452c7279d3d"}}'
@serde
class RecurrancePluginData:
    recurrence: "RecurrancePluginDataInner"


@dataclass
class CardCompletionInfo:
    card_id: str
    template_card_id: Optional[str]
    first_available_at: datetime
    repeat_interval: Optional[timedelta]
    infinitely_repeatable: bool = True
    limit_per_member: Optional[int] = None
    assigned_count: int = 0

    @staticmethod
    def from_card(card: trello.TrelloCard, template_cards: list[trello.TrelloCard]) -> "CardCompletionInfo":
        # Find the first time this card was assigned to the member
        first_available_at = trello.trello_id_to_timestamp(card.id)
        repeat_interval = None

        limit_per_member = None
        for label in card.labels:
            if label.name.startswith("Limit per member:"):
                try:
                    limit_per_member = int(label.name.split("Limit per member:")[1])
                except ValueError:
                    logger.warning(f"Invalid limit per member label on card {card.id}: {label.name}")

        # Find the source card that this card was copied from.
        # TODO: Validate that no two template cards have the same name
        source_card = next((c for c in template_cards if c.name == card.name), None)
        if source_card is not None and source_card.pluginData is not None:
            recurrance_plugin_data_value = next(
                (c for c in source_card.pluginData if c.idPlugin == "57b47fb862d25a30298459b1"), None
            )
            if recurrance_plugin_data_value is not None:
                recurrance_data = from_json(RecurrancePluginData, recurrance_plugin_data_value.value).recurrence
                if recurrance_data.period == "daily":
                    repeat_interval = timedelta(days=recurrance_data.interval)
                elif recurrance_data.period == "weekly":
                    assert recurrance_data.weekdays is not None
                    repeat_interval = timedelta(weeks=recurrance_data.interval) / len(recurrance_data.weekdays)
                elif recurrance_data.period == "monthly":
                    assert recurrance_data.days is not None
                    repeat_interval = timedelta(days=30 * recurrance_data.interval) / len(recurrance_data.days)
                elif recurrance_data.period == "yearly":
                    assert recurrance_data.dates is not None
                    repeat_interval = timedelta(days=365 * recurrance_data.interval) / len(recurrance_data.dates)
                else:
                    logger.warning(f"Unknown recurrance period on card {card.id}: {recurrance_data.period}")

        assigned_count = (
            db_session.execute(
                select(func.count())
                .select_from(TaskDelegationLog)
                .where(TaskDelegationLog.card_id == card.id, TaskDelegationLog.action == "assigned")
            ).scalar_one_or_none()
            or 0
        )

        return CardCompletionInfo(
            card_id=card.id,
            template_card_id=source_card.id if source_card else None,
            first_available_at=first_available_at,
            repeat_interval=repeat_interval,
            infinitely_repeatable=any(label.name == "Infinitely Repeatable" for label in card.labels),
            limit_per_member=limit_per_member,
            assigned_count=assigned_count,
        )


@dataclass
class CardRequirements:
    required: Sequence[Tuple[str, Callable[[TaskContext], bool]]]
    size: int
    introduction_message: Optional[str] = None

    def cannot_satisfy_reason(self, context: TaskContext) -> Optional[str]:
        for name, req in self.required:
            if not req(context):
                return name
        return None

    @staticmethod
    def from_card(card: trello.TrelloCard) -> "CardRequirements":
        labels = {label.name for label in card.labels}
        required: list[Tuple[str, Callable[[TaskContext], bool]]] = []
        size = 4

        # label("Room: Big room").requires(door_opened("UUID") or door_opened("UUID"))
        # label("Room: Textile workshop").requires(door_opened("UUID"))

        # label("Machine: Laser").requires(purchased_product_count("Laser Minutes", member_id=member_id, days=30) > 50)
        # # label("Machine: Laser").ask_before_assigning("Are you using the laser today?")

        # label("Cleaning").score(2 if is_evening() or is_morning() else 1)

        # label("Room Developer: Wood").requires(is_part_of_group("Room Developers: Wood") or is_part_of_group("Styrelsen"))

        # label("Level: 3").requires(previously_completed_tasks(label("Level: 2")) >= 2)
        # label("Level: 3").requires(unique_months_visited() >= 3)

        # label("Level: 2").requires(previously_completed_tasks(label("Level: 1")) >= 3)

        # label("Size: Medium").requires(previously_completed_tasks() >= 5)
        # label("Size: Large").requires(previously_completed_tasks() >= 10)

        # label("Size: Large").size(16)
        # label("Size: Medium").size(8)

        if "Room: Big room" in labels:
            required.append(
                (
                    "Entered lower floor",
                    lambda context: context.member.has_opened_door("243dcac3-107f-4b92-b91d-412e0653755e")
                    or context.member.has_opened_door("ffda9ff6-89b4-4a72-8052-25a46316ebbf"),
                )
            )

        if "Room: Textile workshop" in labels:
            required.append(
                (
                    "Entered upper floor",
                    lambda context: context.member.has_opened_door("1de7a08c-b169-4967-ae02-8082e018d538"),
                )
            )

        if "Room: Metal workshop" in labels:
            required.append(
                (
                    "Entered lower floor/metal workshop",
                    lambda context: context.member.has_opened_door("243dcac3-107f-4b92-b91d-412e0653755e"),
                )
            )

        if "Room: Storage room" in labels:
            required.append(
                (
                    "Entered storage room",
                    lambda context: context.member.has_opened_door("9dc5c8c5-6254-4b68-9290-acdd13e17e0b"),
                )
            )

        if "Machine: Laser" in labels:
            required.append(
                (
                    "Purchased some Laser Minutes recently",
                    lambda context: (context.member.purchased_product_count("Laser Minutes") > 50),
                )
            )

        if "Board member" in labels:
            required.append(
                (
                    "Is a board member",
                    lambda context: context.member.is_in_group("board"),
                )
            )

        if "Room Developer: Wood" in labels:
            required.append(
                (
                    "Wood room developer or board",
                    lambda context: (
                        context.member.is_in_group("Room Developers: Wood") or context.member.is_in_group("board")
                    ),
                )
            )

        if "Level: 3" in labels:
            required.append(
                (
                    "Completed Level: 2 at least twice",
                    lambda context: (context.member.completed_tasks_with_label("Level: 2") >= 2),
                )
            )
            required.append(
                ("Visited at least 3 unique months", lambda context: (context.member.unique_months_visited >= 3))
            )

        if "Level: 2" in labels:
            required.append(
                (
                    "Completed Level: 1 at least three times",
                    lambda context: (context.member.completed_tasks_with_label("Level: 1") >= 3),
                )
            )

        if "Size: Medium" in labels:
            required.append(("Completed at least 5 tasks", lambda context: (context.member.total_completed_tasks >= 5)))
            size = 8

        if "Size: Large" in labels:
            required.append(
                ("Completed at least 10 tasks", lambda context: (context.member.total_completed_tasks >= 10))
            )
            size = 16

        return CardRequirements(required=required, size=size, introduction_message=None)


def visit_events_by_member_id(start: datetime, end: datetime) -> dict[int, list[datetime]]:
    events = (
        db_session.execute(
            select(PhysicalAccessEntry)
            .where(PhysicalAccessEntry.invoked_at >= start)
            .where(PhysicalAccessEntry.invoked_at < end)
            .order_by(PhysicalAccessEntry.invoked_at)
        )
        .scalars()
        .all()
    )

    events_by_member: dict[int, list[PhysicalAccessEntry]] = {}
    for event in events:
        if event.member_id is not None:
            events_by_member.setdefault(event.member_id, []).append(event)

    visits_by_member: dict[int, list[datetime]] = {}
    for member_id, events in events_by_member.items():
        last_event = None
        visits = []
        for event in events:
            if last_event is None or (event.invoked_at - last_event.invoked_at) > timedelta(hours=4):
                # New visit
                visits.append(event.invoked_at)
            last_event = event

        visits_by_member[member_id] = visits

    return visits_by_member


@dataclass
class CannotAssignReason:
    reason: str


@dataclass
class TaskScore:
    can_be_assigned: bool
    cannot_be_assigned_reason: Optional[CannotAssignReason]
    score: float
    total_assignable_visits: int


def task_score(
    card: CardRequirements,
    completion_info: CardCompletionInfo,
    ctx: TaskContext,
    reference_task_assignment_contexts: list[TaskContext],
) -> TaskScore:
    if completion_info.assigned_count > 0 and not completion_info.infinitely_repeatable:
        return TaskScore(
            can_be_assigned=False,
            cannot_be_assigned_reason=CannotAssignReason("Task has already been assigned"),
            score=0,
            total_assignable_visits=0,
        )

    # Check if requirements are satisfied
    reason = card.cannot_satisfy_reason(ctx)
    if reason is not None:
        return TaskScore(
            can_be_assigned=False,
            cannot_be_assigned_reason=CannotAssignReason(reason),
            score=0,
            total_assignable_visits=0,
        )

    if (
        ctx.time < completion_info.first_available_at + timedelta(minutes=10)
        and completion_info.template_card_id is None
    ):
        # Don't assign tasks that just became available, as they may be manually created and might still be manually edited
        return TaskScore(
            can_be_assigned=False,
            cannot_be_assigned_reason=CannotAssignReason("Task just became available"),
            score=0,
            total_assignable_visits=0,
        )

    if completion_info.repeat_interval is not None:
        assert completion_info.repeat_interval.total_seconds() > 0
        elapsed_periods = (
            completion_info.first_available_at - ctx.time
        ).total_seconds() / completion_info.repeat_interval.total_seconds()
    else:
        elapsed_periods = 0

    frequency_days_per_year = float(
        round(
            timedelta(days=365).total_seconds()
            / (completion_info.repeat_interval or timedelta(days=365)).total_seconds()
        )
    )

    # A task that is done once per month should be selected more often than a task that is done once per year.
    score = math.sqrt(frequency_days_per_year)
    # A task that is not getting done in time should have its score increased
    score *= 1 + elapsed_periods

    # Make the scores become a bit more readable by humans
    score *= 100

    # How many members in the recent past have been assignable to this task
    # If many members can do it, the score should be lower. If only a few can do it, the score should be higher.
    total_assignable_visits = sum(
        card.cannot_satisfy_reason(other_ctx) is None for other_ctx in reference_task_assignment_contexts
    )

    score /= max(total_assignable_visits, 1)

    # Score: (weight * frequency * (1 + overdue_frequency_intervals)) / (how many members in the past 30 days have been assignable to this task)
    # Can be assigned task: (last completed task size) - (hours spent at space since last completed task)

    return TaskScore(
        can_be_assigned=True,
        cannot_be_assigned_reason=None,
        score=score,
        total_assignable_visits=total_assignable_visits,
    )


def email_to_slack_user(email: str, slack_client: WebClient) -> Optional[str]:
    # Look up Slack user by email
    try:
        response = slack_client.users_lookupByEmail(email=email)
        id: str = response["user"]["id"]
        return id
    except SlackApiError as e:
        logger.error(f"Failed to look up Slack user by email {email}: {e.response['error']}")
        return None


def send_slack_message_to_member(
    member: Member, trello_card: trello.TrelloCard, log_id: int, slack_interaction: SlackInteraction | None = None
) -> None:
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        logger.warning("No SLACK_BOT_TOKEN configured; skipping Slack send")
        return

    slack_client = WebClient(token=token)
    slack_user = email_to_slack_user(member.email, slack_client)
    if not slack_user:
        logger.info(f"Member {member.email} does not have a Slack account linked.")
        return

    if slack_interaction is None:
        text = f"Hi {member.firstname}! While you're at the makerspace you've been assigned a small task:\n\n*{trello_card.name}*\n{trello_card.desc}\n\nPlease try to do it while you're here."
    else:
        text = f"Ok, here's a new task:\n\n*{trello_card.name}*\n{trello_card.desc}"

    # Convert markdown links to Slack format
    # [link text](url "optional title") -> <url|link text>
    text = re.sub(r'\[(.*?)\]\((\S+)(?:\s+".*?")?\)', r"<\2|\1>", text)

    print(text)
    blocks: list[Block] = [
        SectionBlock(text=MarkdownTextObject(text=text)),
        ActionsBlock(
            elements=[
                ButtonElement(
                    text=PlainTextObject(text="I did it", emoji=True),
                    action_id="task_feedback_done",
                    value=f"{log_id}:done",
                    style="primary",  # Makes the button green
                ),
                StaticSelectElement(
                    placeholder=PlainTextObject(text="I couldn't do it", emoji=True),
                    action_id="task_feedback_not_done",
                    options=[
                        Option(
                            text=PlainTextObject(text="I did something else for the space instead", emoji=True),
                            value=f"{log_id}:not_done_did_something_else",
                        ),
                        Option(
                            text=PlainTextObject(text="I couldn't figure out how", emoji=True),
                            value=f"{log_id}:not_done_confused",
                        ),
                        Option(
                            text=PlainTextObject(text="I forgot", emoji=True),
                            value=f"{log_id}:not_done_forgot",
                        ),
                        Option(
                            text=PlainTextObject(text="I didn't have time", emoji=True),
                            value=f"{log_id}:not_done_no_time",
                        ),
                        Option(
                            text=PlainTextObject(text="Other", emoji=True),
                            value=f"{log_id}:not_done_other",
                        ),
                    ],
                ),
                ButtonElement(
                    text=PlainTextObject(text="↻ Give me something else", emoji=True),
                    action_id="task_feedback_new_task",
                    value=f"{log_id}:new_task",
                ),
            ]
        ),
    ]

    host = config.get("HOST_BACKEND")

    try:
        if slack_interaction is not None:
            # Respond to an existing message
            slack_response = slack_client.chat_update(
                channel=slack_interaction.channel,
                ts=slack_interaction.message.ts,
                text=text,
                blocks=blocks,
            )
        else:
            slack_response = slack_client.chat_postMessage(channel=slack_user, text=text, blocks=blocks)
        print(slack_response)
    except SlackApiError as e:
        logger.error(f"Failed to send Slack message to #{member.member_number}: {e.response['error']}")
        raise

    if not host.startswith("https://"):
        # Likely not a public URL, we are likely in dev mode
        # Post curl commands to emulate the slack button options
        actions = [
            ("task_feedback_done", "done"),
            ("task_feedback_not_done", "not_done_did_something_else"),
            ("task_feedback_not_done", "not_done_confused"),
            ("task_feedback_not_done", "not_done_forgot"),
            ("task_feedback_not_done", "not_done_no_time"),
            ("task_feedback_not_done", "not_done_other"),
            ("task_feedback_new_task", "new_task"),
        ]

        logger.info(f"Dev mode: Use the following curl commands to simulate Slack button actions:")
        for action_type, value in actions:
            new_interaction = SlackInteraction(
                action=SlackInteractionAction(action_id=action_type, value=f"{log_id}:{value}"),
                user=slack_user,
                message=SlackMessage(ts=slack_response.get("ts", "")),
                trigger_id="",
                channel=slack_response.get("channel", ""),
            )
            new_interaction_json = to_json(new_interaction)
            new_interaction_json = new_interaction_json.replace("'", "\\'")  # Poor-man's escaping for curl
            print(
                f"curl -X POST {get_api_url('/tasks/slack/interaction')} -H 'Content-Type: application/json' -d '{new_interaction_json}'"
            )


def delegate_task_for_member(member_id: int, slack_interaction: SlackInteraction | None = None) -> Optional[int]:
    if member_id not in [1537, 1612]:
        logger.info(f"Skipping delegation for member {member_id} (not in test list)")
        return None

    # skip if recently got a task
    # if member_recently_received(member_id, days=3):
    #     logger.info(f"Member {member_id} received a task recently; skipping delegation")
    #     return None

    with db_session.begin_nested() as nested:  # Start a transaction
        trello.refresh_cache()  # ensure fresh data when delegating

        visits = visit_events_by_member_id(datetime.now() - timedelta(days=30), datetime.now())
        ASSIGN_DELAY = timedelta(minutes=3)
        print("Loading reference task assignment contexts")
        reference_task_assignment_contexts = [
            TaskContext.from_cache(m, visit_time + ASSIGN_DELAY)
            for m, visit_times in visits.items()
            for visit_time in visit_times
        ]

        for c in reference_task_assignment_contexts:
            if random() < 0.5:
                c.member.completed_tasks_by_label["Level: 1"] = 3
                c.member.total_completed_tasks += 3

            if random() < 0.3:
                c.member.total_completed_tasks += 10

            c.member.doors_opened_this_visit.add("<UUID>")

        print(len(reference_task_assignment_contexts), len(visits))

        ctx = TaskContext.from_cache(member_id, datetime.now())
        ctx.member.completed_tasks_by_label["Level: 1"] = 3
        ctx.member.completed_tasks_by_label["Level: 2"] = 3
        ctx.member.total_completed_tasks += 10
        ctx.member.doors_opened_this_visit.add("<UUID>")

        print("Loading cards")
        cards = trello.cached_cards(trello.SOURCE_LIST_NAME)
        template_cards = trello.cached_cards(trello.TEMPLATE_LIST_NAME)
        print(f"Loaded {len(cards)} cards")

        t0 = time.time()
        total_weight = 0.0
        picked_card: Optional[trello.TrelloCard] = None

        for card in cards:
            score = task_score(
                CardRequirements.from_card(card),
                CardCompletionInfo.from_card(card, template_cards),
                ctx,
                reference_task_assignment_contexts,
            )
            if score.cannot_be_assigned_reason is not None:
                print(
                    f"Card {card.name} cannot be assigned to member {member_id} because they have not {score.cannot_be_assigned_reason.reason}"
                )
            else:
                print(f"Card {card.name} score for member {member_id}: {score.score:.2f}")
                print(f"\tTotal assignable visits in past 30 days: {score.total_assignable_visits}")

            # Reservoir sampling to pick a card
            total_weight += score.score
            if picked_card is None or random() < (score.score / total_weight):
                picked_card = card

        print()
        if picked_card:
            print(f"Selected card for member {member_id}: {picked_card.name}")
        else:
            print(f"No card selected for member {member_id}")
            return None

        t1 = time.time()
        print(f"Scoring took {t1 - t0:.2f} seconds")

        member = db_session.get(Member, member_id)
        if not member:
            raise ValueError(f"Member {member_id} not found in db")

        # create log entry
        log = TaskDelegationLog(
            member_id=member_id,
            card_id=picked_card.id,
            card_name=picked_card.name,
            action="assigned",
            details=f"",
        )

        db_session.add(log)

        labels = [TaskDelegationLogLabel(log=log, label=label.name) for label in picked_card.labels]
        for label in labels:
            db_session.add(label)

        db_session.flush()  # get id

        # send Slack message
        try:
            send_slack_message_to_member(member, picked_card, log.id, slack_interaction)
        except Exception as e:
            logger.exception("Failed to send Slack message")
            nested.rollback()
            return None

        id: int = log.id

    db_session.commit()
    return id


def mark_ignored_tasks() -> None:
    """
    Mark tasks in the task delegation log as ignored if they are older than a certain threshold.
    This prevents them from being considered for future assignments.
    """
    threshold = datetime.now() - timedelta(days=1)
    logs = (
        db_session.execute(
            select(TaskDelegationLog)
            .where(TaskDelegationLog.action == "assigned")
            .where(TaskDelegationLog.created_at < threshold)
        )
        .scalars()
        .all()
    )

    for log in logs:
        log.action = "ignored"
        db_session.add(log)

    db_session.commit()


def process_new_visits() -> None:
    """
    Look for new physical_access_log entries and delegate tasks for members who visited.
    Uses a Redis-stored last processed ID to avoid reprocessing.
    """
    last_id = int(redis_connection.get(REDIS_LAST_ID_KEY) or b"0")

    print("Last id", last_id)
    # TODO: Only consider recent visits, since the redis data is ephemeral and may be lost on rebuilds of the container
    q = (
        select(PhysicalAccessEntry)
        .where(
            PhysicalAccessEntry.id > last_id, PhysicalAccessEntry.created_at > datetime.now() - timedelta(minutes=20)
        )
        .order_by(PhysicalAccessEntry.id.asc())
    )
    rows = db_session.execute(q).scalars().all()
    max_seen = last_id
    for entry in rows:
        max_seen = max(max_seen, entry.id)
        if entry.member_id is not None:
            delegate_task_for_member(entry.member_id)

    redis_connection.set(REDIS_LAST_ID_KEY, str(max_seen))
    db_session.commit()


if __name__ == "__main__":
    engine = create_mysql_engine(**get_mysql_config())  # type: ignore
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    delegate_task_for_member(1537)
