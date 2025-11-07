import math
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum
from io import BytesIO
from logging import getLogger
from random import random
from typing import Callable, List, Optional, Sequence, Set, Tuple

import requests
from membership.models import Group, Member, member_group
from multiaccessy.models import PhysicalAccessEntry
from PIL import Image
from redis_cache import redis_connection
from serde import field, serde, to_dict
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
    DividerBlock,
    ImageBlock,
    MarkdownTextObject,
    Option,
    PlainTextObject,
    SectionBlock,
    StaticSelectElement,
)
from sqlalchemy import distinct, func, select

from tasks import trello
from tasks.models import TaskDelegationLog, TaskDelegationLogLabel, TaskSize

logger = getLogger("task-delegator")

REDIS_LAST_ID_KEY = "task_delegator_last_id"

# Delay assigning tasks until a short while after the member opens the first door of the makerspace.
# This is to allow time to open other doors, which can provide hints of what areas of the space they are visiting,
# and as such, what tasks would be most relevant to assign.
ASSIGNMENT_DELAY_AFTER_START_OF_VISIT = timedelta(minutes=3)

# Increment this when the structure or semantics of MemberTaskInfo changes, to avoid using stale cached data.
CACHE_VERSION = 4
IMAGE_CACHE_VERSION = 5

TASK_LOG_CHANNEL = config.get("SLACK_TASK_LOG_CHANNEL_ID")
if TASK_LOG_CHANNEL == "":
    TASK_LOG_CHANNEL = None


@serde
class SlackFile:
    id: str
    url: str


@serde
class SlackInteractionAction:
    action_id: str
    value: str


@serde
class SlackMessage:
    ts: str


@serde
class SlackUser:
    id: str


@serde
class SlackChannel:
    id: str


@serde
class SlackInteraction:
    actions: list[SlackInteractionAction]
    user: SlackUser
    message: SlackMessage
    trigger_id: str
    channel: SlackChannel


TASK_SIZE_TO_TIME = {
    TaskSize.SMALL: timedelta(hours=4),
    TaskSize.MEDIUM: timedelta(hours=8),
    TaskSize.LARGE: timedelta(hours=20),
}


@serde
class TaskDelegationLogSimple:
    card_id: str
    template_card_id: str | None
    status: TaskDelegationLog.ACTION_TYPE
    card_name: str
    created_at: datetime
    size: TaskSize

    @staticmethod
    def from_log(log: Optional[TaskDelegationLog]) -> Optional["TaskDelegationLogSimple"]:
        if log is None:
            return None
        return TaskDelegationLogSimple(
            card_id=log.card_id,
            template_card_id=log.template_card_id,
            card_name=log.card_name,
            created_at=log.created_at,
            size=log.task_size,
            status=log.action,
        )

    def matches(self, other: "CardCompletionInfo") -> bool:
        return (
            self.card_id == other.card_id
            or (self.template_card_id is not None and self.template_card_id == other.template_card_id)
            or self.card_name == other.card_name
        )


@serde
class MemberTaskInfo:
    member_id: int

    # Number of tasks that this member has completed
    total_completed_tasks: int

    # Number of tasks with a given label that this member has completed
    completed_tasks_by_label: dict[str, int]

    # Accessy UUIDs of doors that have been opened during this visit.
    # Refers to accessy asset publication ids.
    doors_opened_this_visit: set[str]

    # Number of distinct months the member has visited the space
    unique_months_visited: int

    # Number of distinct days the member has visited the space
    unique_days_visited: int

    # Names of makeradmin groups that the member is part of
    groups: set[str]

    # Last task assigned to the member, regardless of completion status
    last_assigned_task: Optional[TaskDelegationLogSimple]

    # Last task that was definitely completed
    last_completed_task: Optional[TaskDelegationLogSimple]

    # Total count of products purchased recently, by product name
    purchased_product_count_by_name: dict[str, int]

    # Number of times this member has completed tasks, by trello card id.
    # Includes both card instance ids and template card ids.
    completed_card_ids: dict[str, int]

    # Number of times this member has completed tasks, by trello card name.
    completed_card_names: dict[str, int]

    # Number of hours spent at the space since the day after the last task was either assigned or completed
    # If the member has never completed a task, this will be a very large value.
    time_at_space_since_last_task: timedelta = field(
        serializer=lambda td: td.total_seconds(), deserializer=lambda seconds: timedelta(seconds=seconds)
    )

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
                    PhysicalAccessEntry.created_at <= now,
                )
            ).scalar_one()
            or 0
        )

        unique_days_visited = (
            db_session.execute(
                select(func.count(distinct(func.date_format(PhysicalAccessEntry.created_at, "%Y-%m-%d")))).where(
                    PhysicalAccessEntry.member_id == member_id,
                    PhysicalAccessEntry.created_at <= now,
                )
            ).scalar_one()
            or 0
        )

        last_completed_task = db_session.execute(
            select(TaskDelegationLog)
            .where(
                TaskDelegationLog.member_id == member_id,
                TaskDelegationLog.action == "completed",
                TaskDelegationLog.created_at <= now,
            )
            .order_by(TaskDelegationLog.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        last_assigned_task = db_session.execute(
            select(TaskDelegationLog)
            .where(
                TaskDelegationLog.member_id == member_id,
                TaskDelegationLog.created_at <= now,
            )
            .order_by(TaskDelegationLog.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_assigned_task is not None:
            day_after_last_task = last_assigned_task.created_at
            day_after_last_task += timedelta(days=1)
            day_after_last_task.replace(hour=0, minute=0, second=0, microsecond=0)

            visits = visit_events_by_member_id(day_after_last_task, now, member_id=member_id).get(member_id, [])
            time_at_space_since_last_task = timedelta()
            for _, duration in visits:
                time_at_space_since_last_task += duration
        else:
            time_at_space_since_last_task = timedelta(days=365 * 10)  # A large value representing "infinity"

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

        completed_logs = (
            db_session.execute(
                select(TaskDelegationLog).where(
                    TaskDelegationLog.member_id == member_id,
                    TaskDelegationLog.action == "completed",
                    TaskDelegationLog.created_at <= now,
                )
            )
            .scalars()
            .all()
        )

        completed_card_ids: dict[str, int] = {}
        completed_card_names: dict[str, int] = {}
        for log in completed_logs:
            completed_card_ids[log.card_id] = completed_card_ids.get(log.card_id, 0) + 1
            if log.template_card_id is not None:
                completed_card_ids[log.template_card_id] = completed_card_ids.get(log.template_card_id, 0) + 1
            completed_card_names[log.card_name] = completed_card_names.get(log.card_name, 0) + 1

        return MemberTaskInfo(
            member_id=member.member_id,
            total_completed_tasks=total_completed_tasks,
            completed_tasks_by_label=completed_tasks_by_label,
            doors_opened_this_visit=doors_opened_this_visit,
            unique_months_visited=unique_months_visited,
            unique_days_visited=unique_days_visited,
            groups=groups,
            last_completed_task=TaskDelegationLogSimple.from_log(last_completed_task),
            last_assigned_task=TaskDelegationLogSimple.from_log(last_assigned_task),
            purchased_product_count_by_name=purchased_product_count_by_name,
            completed_card_ids=completed_card_ids,
            completed_card_names=completed_card_names,
            time_at_space_since_last_task=time_at_space_since_last_task,
        )


@dataclass
class TaskContext:
    member: MemberTaskInfo
    time: datetime

    @staticmethod
    def from_cache(member_id: int, now: datetime) -> "TaskContext":
        cache_key = f"member_task_info:{CACHE_VERSION}:{member_id}:{now.date().strftime('%Y-%m-%dT%H')}"
        cached = redis_connection.get(cache_key)
        if cached:
            info = from_json(MemberTaskInfo, cached)
        else:
            info = MemberTaskInfo.from_member(member_id, now)

            # This data should be immutable, as it represents a state at a given time in the past.
            # But we let it expire after some time anyway, to avoid potential issues and to get rid of unused data after a while.
            redis_connection.setex(cache_key, timedelta(days=60), to_json(info))
        return TaskContext(member=info, time=now)

    @staticmethod
    def from_member(member_id: int, now: datetime) -> "TaskContext":
        info = MemberTaskInfo.from_member(member_id, now)
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
    # Trello card ID
    card_id: str

    # If this card was created from a template card, the ID of that template card.
    # Template cards are used for repeat tasks, and a new card instance will be created
    # each repeat cycle.
    template_card_id: Optional[str]

    # Trello card name
    card_name: str

    # The first time this instance of the task was available to be assigned.
    # For a repeat task, this is the time when the last repeat cycle began.
    first_available_at: datetime

    present_members_with_experience: list[Member]

    # If set, the average interval at which this task repeats.
    # If not set, the task is likely a one-off task.
    repeat_interval: Optional[timedelta]

    # True if the task can be repeated many times by the same or different members.
    # It will not be moved to the Done list once completed.
    infinitely_repeatable: bool = True

    # How many times an individual member can complete this task.
    limit_per_member: Optional[int] = None

    # How many members are assigned to this this specific task right now.
    # Will typically only be 0 or 1, unless the task is infinitely repeatable
    assigned_count: int = 0

    # How many times this specific task has been completed.
    # This does not count repeat completions of the same template card.
    completed_count: int = 0

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

        # Find the template card that this card was copied from.
        # TODO: Validate that no two template cards have the same name
        template_card = next((c for c in template_cards if c.name == card.name), None)

        if template_card is not None and template_card.id == card.id:
            logger.error(
                f"Card {card.id} has itself as template card. Some list names in the trello config must be incorrect."
            )
            template_card = None

        if template_card is not None and template_card.pluginData is not None:
            recurrance_plugin_data_value = next(
                (c for c in template_card.pluginData if c.idPlugin == "57b47fb862d25a30298459b1"), None
            )
            if recurrance_plugin_data_value is not None:
                if recurrance_plugin_data_value.value == "{}":
                    logger.warning(f"Empty recurrance plugin data on card {card.name} ({card.id})")
                else:
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

        completed_count = (
            db_session.execute(
                select(func.count())
                .select_from(TaskDelegationLog)
                .where(TaskDelegationLog.card_id == card.id, TaskDelegationLog.action == "completed")
            ).scalar_one_or_none()
            or 0
        )

        present_members_with_experience = list(
            db_session.execute(
                select(Member, func.count())
                .join(TaskDelegationLog, TaskDelegationLog.member_id == Member.member_id)
                .where(
                    (
                        (TaskDelegationLog.card_id == card.id)
                        | (TaskDelegationLog.template_card_id == (template_card or card).id)
                    ),
                    TaskDelegationLog.action == "completed",
                )
                .join(PhysicalAccessEntry, PhysicalAccessEntry.member_id == Member.member_id)
                .where(PhysicalAccessEntry.created_at >= datetime.now() - timedelta(minutes=90))
                .group_by(Member.member_id)
            )
            .tuples()
            .all()
        )
        present_members_with_experience.sort(key=lambda pair: pair[1], reverse=True)

        return CardCompletionInfo(
            card_name=card.name,
            card_id=card.id,
            template_card_id=template_card.id if template_card else None,
            first_available_at=first_available_at,
            repeat_interval=repeat_interval,
            infinitely_repeatable=any(label.name == "Infinitely Repeatable" for label in card.labels),
            limit_per_member=limit_per_member,
            assigned_count=assigned_count,
            completed_count=completed_count,
            present_members_with_experience=[pair[0] for pair in present_members_with_experience],
        )


@dataclass
class CardRequirements:
    required: Sequence[Tuple[str, Callable[[TaskContext], bool]]]
    size: TaskSize
    introduction_message: list[Callable[[TaskContext], str | None]]
    completion_message: list[Callable[[TaskContext], str | None]]
    description: str

    def can_satisfy(self, context: TaskContext) -> bool:
        for _, req in self.required:
            if not req(context):
                return False
        return True

    def cannot_satisfy_reasons(self, context: TaskContext) -> list[str]:
        reasons = []
        for name, req in self.required:
            if not req(context):
                reasons.append(name)
        return reasons

    def introduction_messages_for_context(self, context: TaskContext) -> list[str]:
        messages = []
        for msg_fn in self.introduction_message:
            msg = msg_fn(context)
            if msg is not None:
                messages.append(msg)
        return messages

    def completion_messages_for_context(self, context: TaskContext) -> list[str]:
        messages = []
        for msg_fn in self.completion_message:
            msg = msg_fn(context)
            if msg is not None:
                messages.append(msg)
        return messages

    @staticmethod
    def from_card(card: trello.TrelloCard) -> "CardRequirements":
        labels = {label.name for label in card.labels}
        required: list[Tuple[str, Callable[[TaskContext], bool]]] = []
        size = TaskSize.SMALL
        completion_message: list[Callable[[TaskContext], str | None]] = []
        introduction_message: list[Callable[[TaskContext], str | None]] = []

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
                    "Hasn't entered lower floor",
                    lambda context: context.member.has_opened_door("243dcac3-107f-4b92-b91d-412e0653755e")
                    or context.member.has_opened_door("ffda9ff6-89b4-4a72-8052-25a46316ebbf"),
                )
            )

        if "Room: Textile workshop" in labels:
            required.append(
                (
                    "Hasn't entered upper floor",
                    lambda context: context.member.has_opened_door("1de7a08c-b169-4967-ae02-8082e018d538"),
                )
            )

        if "Room: Wood workshop" in labels:
            required.append(
                (
                    "Hasn't entered lower floor",
                    lambda context: context.member.has_opened_door("243dcac3-107f-4b92-b91d-412e0653755e")
                    or context.member.has_opened_door("ffda9ff6-89b4-4a72-8052-25a46316ebbf"),
                )
            )

            required.append(
                (
                    "Wood workshop is closed to non-developers at the moment",
                    lambda context: context.member.is_in_group("room_developers_wood"),
                )
            )

        if "Room: Metal workshop" in labels:
            required.append(
                (
                    "Hasn't entered lower floor/metal workshop",
                    lambda context: context.member.has_opened_door("243dcac3-107f-4b92-b91d-412e0653755e"),
                )
            )

        if "Room: Storage room" in labels:
            required.append(
                (
                    "Hasn't entered storage room",
                    lambda context: context.member.has_opened_door("9dc5c8c5-6254-4b68-9290-acdd13e17e0b"),
                )
            )

        if "Machine: Laser" in labels:
            required.append(
                (
                    "Hasn't purchased Laser cutter usage recently",
                    lambda context: (context.member.purchased_product_count("Laser cutter usage") > 50),
                )
            )

        if "Board member" in labels:
            required.append(
                (
                    "Is not a board member",
                    lambda context: context.member.is_in_group("board"),
                )
            )

        if "Room Developer: Wood" in labels:
            required.append(
                (
                    "Is not a wood room developer or board member",
                    lambda context: (
                        context.member.is_in_group("room_developers_wood") or context.member.is_in_group("board")
                    ),
                )
            )

        if "Level: 3" in labels:
            required.append(
                (
                    "Has not completed Level: 2 tasks at least twice",
                    lambda context: (context.member.completed_tasks_with_label("Level: 2") >= 2),
                )
            )
            required.append(
                (
                    "Has visited the space fewer than 3 unique months",
                    lambda context: (context.member.unique_months_visited >= 3),
                )
            )

            if "Room: Wood workshop" in labels:
                required.append(
                    (
                        "Has not completed wood workshop tasks at least twice",
                        lambda context: (context.member.completed_tasks_with_label("Room: Wood workshop") >= 2),
                    )
                )

            completion_message.append(
                lambda context: "Congratulations on completing your *first Level 3 task*! Thanks for contributing to keeping the makerspace running! :sunglasses:"
                if context.member.completed_tasks_with_label("Level: 3") == 1
                else None
            )

        if "Level: 2" in labels:
            required.append(
                (
                    "Has not completed Level: 1 tasks at least thrice",
                    lambda context: (context.member.completed_tasks_with_label("Level: 1") >= 3),
                )
            )

            if "Room: Wood workshop" in labels:
                required.append(
                    (
                        "Has not completed wood workshop tasks at least once",
                        lambda context: (context.member.completed_tasks_with_label("Room: Wood workshop") >= 1),
                    )
                )

            completion_message.append(
                lambda context: "Congratulations on completing your *first Level 2 task*! Thanks for contributing to keeping the makerspace running! :tada:"
                if context.member.completed_tasks_with_label("Level: 2") == 1
                else None
            )

        if "Level: 1" in labels:
            required.append(
                (
                    "Has not completed Level: Intro1 tasks",
                    lambda context: (context.member.completed_tasks_with_label("Level: Intro1") >= 1),
                )
            )

            completion_message.append(
                lambda context: "Congratulations on completing your *first Level 1 task*! Thanks a lot for helping out! :star2:"
                if context.member.completed_tasks_with_label("Level: 1") == 1
                else None
            )

        if "Size: Medium" in labels:
            required.append(
                ("Has completed fewer than 5 tasks", lambda context: (context.member.total_completed_tasks >= 5))
            )
            size = TaskSize.MEDIUM

            introduction_message.append(
                lambda context: "This is a medium-sized task, which may require some additional effort compared to smaller tasks. Thank you for taking the time to help out! If you complete this, it will take longer until you are given another task."
            )

        if "Size: Large" in labels:
            required.append(
                ("Has completed fewer than 10 tasks", lambda context: (context.member.total_completed_tasks >= 10))
            )
            size = TaskSize.LARGE

            introduction_message.append(
                lambda context: "This is a large task, which may require additional effort and time to complete. Completing this task will mean that you won't be assigned another task for a longer period."
            )
            completion_message.append(
                lambda context: "Congratulations on completing a large task! Your effort is greatly appreciated and helps keep the makerspace running smoothly! :tada:"
            )

        # Extract "Requires" instructions from the card description
        # For example "Requires: [https://trello.com/c/hKtltoHX/58-get-a-wiki-account](https://trello.com/c/hKtltoHX/58-get-a-wiki-account "smartCard-inline")"
        requires_pattern = re.compile(r"Requires:\s*\[(https?://\S+)\]\(https?://\S+(?:\s+\".*?\")?\)")

        desc = card.desc or ""
        requires_matches = requires_pattern.findall(desc)

        for match in requires_matches:
            if not match.startswith("https://trello.com/c/"):
                logger.error(f"Invalid URL in 'Requires' instruction (not a Trello URL): {match}")
                continue

            # TODO: This is not the same type of id as used in Trello API calls. Need to convert.
            card_id = match.split("/")[-2]
            if not re.match(r"^[a-zA-Z0-9]+$", card_id):
                logger.error(
                    f"Invalid Trello card URL in 'Requires' instruction: {match}. Found card id='{card_id}', but that doesn't look like a valid card id."
                )
                continue

            required.append(
                (
                    f"Has not completed required card {card_id}",
                    lambda context: context.member.completed_card_ids.get(card_id, 0) > 0,
                )
            )

        # Remove "Requires" instructions from the description
        desc = requires_pattern.sub("", desc).strip()

        return CardRequirements(
            required=required,
            size=size,
            introduction_message=introduction_message,
            completion_message=completion_message,
            description=desc,
        )


def member_recently_received_task(ctx: TaskContext) -> bool:
    # If a member has completed a task recently, don't assign them another one too soon.
    # The wait depends on the size of the task
    if ctx.member.last_completed_task is not None:
        if ctx.member.time_at_space_since_last_task < TASK_SIZE_TO_TIME[ctx.member.last_completed_task.size]:
            return True

    if ctx.member.last_assigned_task is not None:
        # If a member has an assigned task that they haven't completed yet, don't assign them another one.
        # Tasks that are ignored will be marked as such after some time, so this only applies to recently assigned tasks.
        if ctx.member.last_assigned_task.status == "assigned":
            return True

        # If a member has been assigned (but not necessarily completed) a task recently, don't assign them another one too soon.
        # This can be relevant if a member quickly says that they cannot complete a task for some reason.
        # It's then no longer assigned or completed, but we still don't want to assign them another task too soon.
        if ctx.time - ctx.member.last_assigned_task.created_at < timedelta(hours=14):
            return True

    return False


def visit_events_by_member_id(
    start: datetime, end: datetime, member_id: int | None = None
) -> dict[int, list[Tuple[datetime, timedelta]]]:
    q = (
        select(PhysicalAccessEntry)
        .where(PhysicalAccessEntry.invoked_at >= start)
        .where(PhysicalAccessEntry.invoked_at < end)
        .order_by(PhysicalAccessEntry.invoked_at)
    )
    if member_id is not None:
        q = q.where(PhysicalAccessEntry.member_id == member_id)

    events = db_session.execute(q).scalars().all()

    events_by_member: dict[int, list[PhysicalAccessEntry]] = {}
    for event in events:
        if event.member_id is not None:
            events_by_member.setdefault(event.member_id, []).append(event)

    visits_by_member: dict[int, list[Tuple[datetime, timedelta]]] = {}
    for member_id, events in events_by_member.items():
        last_event: PhysicalAccessEntry | None = None
        visits = []
        start_of_current_visit = None

        def add_visit(start: datetime, end: datetime) -> None:
            duration = end - start
            duration += timedelta(minutes=90)  # Assume some extra time after last door open
            visits.append((start, duration))

        for event in events:
            if last_event is None or (event.invoked_at - last_event.invoked_at) > timedelta(hours=4):
                # New visit
                if start_of_current_visit is not None and last_event is not None:
                    add_visit(start_of_current_visit, last_event.created_at)
                start_of_current_visit = event.invoked_at

            last_event = event

        if start_of_current_visit is not None and last_event is not None:
            add_visit(start_of_current_visit, last_event.created_at)

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
    requirements: CardRequirements,
    completion_info: CardCompletionInfo,
    ctx: TaskContext,
    reference_task_assignment_contexts: list[TaskContext],
    ignore_reasons: List[str],
) -> TaskScore:
    if (
        completion_info.assigned_count > 0
        and not completion_info.infinitely_repeatable
        and not "Task has already been assigned" in ignore_reasons
    ):
        return TaskScore(
            can_be_assigned=False,
            cannot_be_assigned_reason=CannotAssignReason("Task has already been assigned"),
            score=0,
            total_assignable_visits=0,
        )

    # This primarily guards against an out-of-date trello cache.
    # If someone completes a task, and we don't update the trello cache before the next task assignment,
    # we don't want to try to assign the same task again.
    if (
        completion_info.completed_count > 0
        and not completion_info.infinitely_repeatable
        and not "Task has already been completed" in ignore_reasons
    ):
        return TaskScore(
            can_be_assigned=False,
            cannot_be_assigned_reason=CannotAssignReason("Task has already been completed"),
            score=0,
            total_assignable_visits=0,
        )

    limit_per_member = completion_info.limit_per_member
    if (
        limit_per_member is not None
        and (
            ctx.member.completed_card_ids.get(completion_info.card_id, 0) >= limit_per_member
            or (
                completion_info.template_card_id is not None
                and ctx.member.completed_card_ids.get(completion_info.template_card_id, 0) >= limit_per_member
            )
            or ctx.member.completed_card_names.get(completion_info.card_name, 0) >= limit_per_member
        )
        and not "Task has already been completed the maximum number of times by this member" in ignore_reasons
    ):
        return TaskScore(
            can_be_assigned=False,
            cannot_be_assigned_reason=CannotAssignReason(
                "Task has already been completed the maximum number of times by this member"
            ),
            score=0,
            total_assignable_visits=0,
        )

    # Check if requirements are satisfied
    reasons = requirements.cannot_satisfy_reasons(ctx)
    reasons = [r for r in reasons if r not in ignore_reasons]
    if reasons:
        return TaskScore(
            can_be_assigned=False,
            cannot_be_assigned_reason=CannotAssignReason(", ".join(reasons)),
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
        equivalent_repeat_interval = completion_info.repeat_interval
    else:
        if completion_info.infinitely_repeatable:
            # Assign a default repeat interval for infinitely repeatable one-off tasks
            equivalent_repeat_interval = timedelta(days=30)
        else:
            # Assign a default repeat interval for one-off tasks
            equivalent_repeat_interval = timedelta(days=180)
        elapsed_periods = 0

    frequency_days_per_year = float(
        round(timedelta(days=365).total_seconds() / equivalent_repeat_interval.total_seconds())
    )

    # A task that is done once per month should be selected more often than a task that is done once per year.
    score = math.sqrt(frequency_days_per_year)
    # A task that is not getting done in time should have its score increased
    score *= 1 + elapsed_periods

    # Avoid assigning the same task twice in a row (regardless of completion status)
    # and avoid assigning the same task as the last completed task
    same_as_last_assigned_task = ctx.member.last_assigned_task is not None and ctx.member.last_assigned_task.matches(
        completion_info
    )
    same_as_last_completed_task = ctx.member.last_completed_task is not None and ctx.member.last_completed_task.matches(
        completion_info
    )

    if same_as_last_assigned_task or same_as_last_completed_task:
        score *= 0.1

    present_other_members_with_experience = [
        m for m in completion_info.present_members_with_experience if m.member_id != ctx.member.member_id
    ]

    # If there are members present who have experience with this task, this is a good time to assign it,
    # because the member can ask them for help if needed.
    score_multiplier_by_members_present = [1, 3, 4, 4.5]
    score *= score_multiplier_by_members_present[
        min(len(present_other_members_with_experience), len(score_multiplier_by_members_present) - 1)
    ]

    # Make the scores become a bit more readable by humans
    score *= 100

    # How many members in the recent past have been assignable to this task
    # If many members can do it, the score should be lower. If only a few can do it, the score should be higher.
    total_assignable_visits = sum(
        requirements.can_satisfy(other_ctx) for other_ctx in reference_task_assignment_contexts
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


def lookup_slack_user_by_email(email: str, slack_client: WebClient) -> Optional[str]:
    # Look up Slack user by email
    try:
        response = slack_client.users_lookupByEmail(email=email)
        id: str = response["user"]["id"]
        return id
    except SlackApiError as e:
        logger.error(f"Failed to look up Slack user by email {email}: {e.response['error']}")
        return None


@dataclass
class DownloadedAttachment:
    url: str
    data: bytes
    mime_type: str


# def download_attachment(attachment: trello.TrelloAttachment) -> DownloadedAttachment:
#     cache_key = f"trello_attachment_cache:{CACHE_VERSION}:{attachment.url}"
#     cached_data = redis_connection.get(cache_key)
#     if cached_data:
#         return cached_data

#     response = requests.get(attachment.url)
#     response.raise_for_status()
#     data = response.content
#     redis_connection.setex(cache_key, timedelta(days=20), data)
#     return DownloadedAttachment(url=attachment.url, data=data, mime_type=attachment.mime_type)


def convert_trello_markdown_to_slack_markdown(text: str) -> str:
    """Ah, yes. Markdown. The one true universal format that everyone agrees on..."""
    # Convert markdown links to Slack format
    # [link text](url "optional title") -> <url|link text>
    text = re.sub(r'\[(.*?)\]\((\S+)(?:\s+".*?")?\)', r"<\2|\1>", text)

    # Convert Trello bold (**bold**) to Slack bold (*bold*)
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)

    return text


SLACK_UPLOADED_FILE_TTL = timedelta(days=60)


def upload_image_to_slack(trello_attachment: trello.TrelloAttachment, slack_client: WebClient) -> Optional[str]:
    """
    Download an image from Trello and upload it to Slack. Cache the Slack URL in Redis.
    """
    logger.info(f"Uploading Trello image {trello_attachment.url} to Slack...")
    cache_key = f"slack_image_cache:{IMAGE_CACHE_VERSION}:{trello_attachment.url}"
    cached_slack_url = redis_connection.get(cache_key)

    if cached_slack_url:
        # Refresh the expiration time for the cached Slack URL
        redis_connection.expire(cache_key, SLACK_UPLOADED_FILE_TTL)
        return cached_slack_url.decode("utf-8")

    # Download the image from Trello
    try:
        data = trello.download_attachment(trello_attachment)
    except requests.RequestException as e:
        logger.error(f"Failed to download Trello attachment {trello_attachment.url}: {e}")
        return None

    logger.info(f"\tDownloaded {len(data)} bytes from Trello.")

    # Resize the image to at most 1000px wide or tall
    try:
        image = Image.open(BytesIO(data))
        original_size = image.size
        image.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        resized_buffer = BytesIO()
        image.save(resized_buffer, format="PNG" if image.has_transparency_data else image.format or "JPEG")
        data = resized_buffer.getvalue()
        logger.info(f"Resized image from {original_size} to {image.size}")
    except Exception as e:
        logger.error(f"Failed to resize image: {e}")
        return None

    # Upload the image to Slack
    try:
        slack_response = slack_client.files_upload_v2(
            file=data,
            filename=trello_attachment.name,
            title=trello_attachment.name,
        )
        slack_url: str | None = slack_response["file"]["permalink"]
        slack_image_id: str | None = slack_response["file"]["id"]
        if not slack_url or not slack_image_id:
            logger.error(f"Failed to upload image to Slack: {slack_response}")
            return None

        # Poll the file info until the mimetype is set. The upload is asynchronous and will fail if we try to use the file too quickly.
        # See https://github.com/slackapi/java-slack-sdk/issues/1349
        for _ in range(10):  # Retry up to 10 times
            try:
                file_info = slack_client.files_info(file=slack_image_id)
                mime_type = file_info["file"].get("mimetype")
                if mime_type:
                    break
            except SlackApiError as e:
                logger.error(f"Failed to fetch file info for Slack file {slack_image_id}: {e.response['error']}")
                return None
            time.sleep(2)  # Wait for 2 seconds before retrying
        else:
            logger.error(f"Timed out waiting for mimetype to be set for Slack file {slack_image_id}")
            return None

        # Cache the Slack URL in Redis
        # res = SlackFile(id=slack_image_id, url=slack_url)
        redis_connection.setex(cache_key, SLACK_UPLOADED_FILE_TTL, slack_url)

        logger.info(f"\tUploaded image to Slack: {slack_url} (id={slack_image_id})")
        return slack_url
    except SlackApiError as e:
        logger.error(f"Failed to upload image to Slack: {e.response['error']}")
        return None


def send_slack_message_to_member(
    member: Member,
    ctx: TaskContext,
    trello_card: trello.TrelloCard,
    completion: CardCompletionInfo,
    slack_interaction: SlackInteraction | None = None,
) -> Optional[Tuple[str, str]]:
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        logger.warning("No SLACK_BOT_TOKEN configured; skipping Slack send")
        return None

    slack_client = WebClient(token=token)
    slack_user = lookup_slack_user_by_email(member.email, slack_client)
    if not slack_user:
        logger.info(f"Member {member.email} does not have a Slack account linked.")
        return None

    requirements = CardRequirements.from_card(trello_card)

    if slack_interaction is None:
        size_str = " small" if requirements.size == TaskSize.SMALL else ""
        text = f"Hi {member.firstname}! While you're at the makerspace you've been assigned a{size_str} task:\n\n*{trello_card.name}*\n{trello_card.desc}\n\nPlease try to do it while you're here."
    else:
        text = f"Ok, here's a new task:\n\n*{trello_card.name}*\n{trello_card.desc}"

    text = convert_trello_markdown_to_slack_markdown(text)

    # Upload Trello attachments to Slack and prepare image blocks
    image_blocks = []
    for attachment in trello_card.attachments or []:
        if attachment.mimeType.startswith("image/"):
            slack_file = upload_image_to_slack(attachment, slack_client)
            if slack_file:
                image_blocks.append(
                    ImageBlock(
                        slack_file={"url": slack_file},
                        alt_text="Illustrative image",
                    )
                )

    help_block = None
    if completion.present_members_with_experience:
        slack_members = [
            lookup_slack_user_by_email(m.email, slack_client) for m in completion.present_members_with_experience[:10]
        ]
        slack_members = [m for m in slack_members if m is not None]
        slack_members = slack_members[:3]

        if len(slack_members) == 1:
            experienced_members = f"<@{slack_members[0]}>"
        else:
            experienced_members = ", ".join(f"<@{m}>" for m in slack_members[:-1])
            if len(slack_members) > 1:
                experienced_members += f" or <@{slack_members[-1]}>"

        help_text = f"If you need help with this task, you can ask {experienced_members} who have done it before, and they should be at the space right now."
        help_block = SectionBlock(text=MarkdownTextObject(text=help_text))

    blocks: list[Block] = [
        DividerBlock(),
        SectionBlock(text=MarkdownTextObject(text=text)),
        *[
            SectionBlock(text=MarkdownTextObject(text=text))
            for text in requirements.introduction_messages_for_context(ctx)
        ],
        *([help_block] if help_block is not None else []),
        ActionsBlock(
            elements=[
                ButtonElement(
                    text=PlainTextObject(text="I did it", emoji=True),
                    action_id="task_feedback_done",
                    value=f"done",
                    style="primary",  # Makes the button green
                ),
                StaticSelectElement(
                    placeholder=PlainTextObject(text="I couldn't do it", emoji=True),
                    action_id="task_feedback_not_done",
                    options=[
                        Option(
                            text=PlainTextObject(text="I did something else for the space instead", emoji=True),
                            value=f"not_done_did_something_else",
                        ),
                        Option(
                            text=PlainTextObject(text="I couldn't figure out how", emoji=True),
                            value=f"not_done_confused",
                        ),
                        Option(
                            text=PlainTextObject(text="I forgot", emoji=True),
                            value=f"not_done_forgot",
                        ),
                        Option(
                            text=PlainTextObject(text="I didn't have time", emoji=True),
                            value=f"not_done_no_time",
                        ),
                        Option(
                            text=PlainTextObject(text="Other", emoji=True),
                            value=f"not_done_other",
                        ),
                    ],
                ),
                ButtonElement(
                    text=PlainTextObject(text="↻ Give me something else", emoji=True),
                    action_id="task_feedback_new_task",
                    value=f"new_task",
                ),
            ]
        ),
        *image_blocks,  # Add image blocks to the message
    ]

    host = config.get("HOST_BACKEND")

    try:
        if slack_interaction is not None:
            # Respond to an existing message
            slack_response = slack_client.chat_update(
                channel=slack_interaction.channel.id,
                ts=slack_interaction.message.ts,
                text=text,
                blocks=blocks,
            )
        else:
            slack_response = slack_client.chat_postMessage(channel=slack_user, text=text, blocks=blocks)
    except SlackApiError as e:
        logger.error(f"Failed to send Slack message to #{member.member_number}: {e.response['error']}")
        raise

    channel = slack_response.get("channel", "")
    ts = slack_response.get("ts", "")
    assert channel is not None
    assert ts is not None

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
                actions=[SlackInteractionAction(action_id=action_type, value=f"{value}")],
                user=SlackUser(id=slack_user),
                message=SlackMessage(ts=ts),
                trigger_id="",
                channel=SlackChannel(id=channel),
            )
            new_interaction_json = to_json(new_interaction)
            new_interaction_json = new_interaction_json.replace("'", "\\'")  # Poor-man's escaping for curl
            print(
                f"curl -X POST {get_api_url('/tasks/slack/interaction')} -H 'Content-Type: application/x-www-form-urlencoded' --data-urlencode 'payload={new_interaction_json}'"
            )

    return (channel, ts)


def select_card_for_member(ctx: TaskContext, ignore_reasons: list[str]) -> Optional[trello.TrelloCard]:
    member_id = ctx.member.member_id
    visits = visit_events_by_member_id(datetime.now() - timedelta(days=30), datetime.now())

    ASSIGN_DELAY = timedelta(minutes=3)
    reference_task_assignment_contexts = [
        TaskContext.from_cache(m, visit_time + ASSIGN_DELAY)
        for m, visit_times in visits.items()
        for (visit_time, _) in visit_times
    ]

    cards = trello.cached_cards(trello.SOURCE_LIST_NAME)
    template_cards = trello.cached_cards(trello.TEMPLATE_LIST_NAME)
    print(f"Loaded {len(cards)} cards")

    total_weight = 0.0
    picked_card: Optional[trello.TrelloCard] = None

    scores = [
        (
            card,
            task_score(
                CardRequirements.from_card(card),
                CardCompletionInfo.from_card(card, template_cards),
                ctx,
                reference_task_assignment_contexts,
                ignore_reasons,
            ),
        )
        for card in cards
    ]

    scores.sort(
        key=lambda s: (
            s[1].score,
            s[1].cannot_be_assigned_reason.reason if s[1].cannot_be_assigned_reason is not None else "",
        ),
        reverse=True,
    )

    for card, score in scores:
        if score.cannot_be_assigned_reason is not None:
            print(f"    N/A: {card.name.ljust(60)} {score.cannot_be_assigned_reason.reason}")
        else:
            print(
                f"{score.score:7.2f} {score.total_assignable_visits * 100 / max(1, len(reference_task_assignment_contexts)):3.0f}%: {card.name}"
            )

            # Use reservoir sampling to pick a card randomly with weights
            total_weight += score.score
            rnd = random()
            if picked_card is None or rnd < (score.score / total_weight):
                picked_card = card

    return picked_card


def delegate_task_for_member(
    member_id: int,
    slack_interaction: SlackInteraction | None = None,
    force: bool = False,
    ignore_reasons: list[str] = [],
) -> Optional[int]:
    ctx = TaskContext.from_member(member_id, datetime.now())

    if not ctx.member.is_in_group("task_beta_testers"):
        logger.info(f"Skipping task delegation for member {member_id} (not in test list)")
        return None

    # skip if recently got a task
    if member_recently_received_task(ctx) and not force and slack_interaction is None:
        logger.info(f"Member {member_id} received a task recently; skipping delegation")
        return None

    trello.refresh_cache()  # ensure fresh data when delegating
    picked_card = select_card_for_member(ctx, ignore_reasons)

    print()
    if picked_card:
        print(f"Selected card for member {member_id}: {picked_card.name}")
        completion = CardCompletionInfo.from_card(picked_card, trello.cached_cards(trello.TEMPLATE_LIST_NAME))
        log_id = assign_task_to_member(ctx, picked_card, completion, slack_interaction)
        return log_id
    else:
        print(f"No card selected for member {member_id}")
        return None


def assign_task_to_member(
    ctx: TaskContext,
    card: trello.TrelloCard,
    card_completion: CardCompletionInfo,
    slack_interaction: SlackInteraction | None,
) -> Optional[int]:
    member_id = ctx.member.member_id
    member = db_session.get(Member, member_id)
    if not member:
        raise ValueError(f"Member {member_id} not found in db")

    with db_session.begin_nested() as nested:  # Start a transaction
        # create log entry
        log = TaskDelegationLog(
            member_id=member_id,
            card_id=card.id,
            card_name=card.name,
            template_card_id=card_completion.template_card_id,
            task_size=CardRequirements.from_card(card).size,
            action="assigned",
            details=f"",
            slack_channel_id=None,
            slack_message_ts=None,
        )

        db_session.add(log)

        labels = [TaskDelegationLogLabel(log=log, label=label.name) for label in card.labels]
        for label in labels:
            db_session.add(label)

        db_session.flush()  # get id

        # send Slack message
        try:
            data = send_slack_message_to_member(member, ctx, card, card_completion, slack_interaction)
            if data is None:
                nested.rollback()
                return None

            channel, message_ts = data
            log.slack_channel_id = channel
            log.slack_message_ts = message_ts
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
    This allows them to be assigned to other members.
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

    token = config.get("SLACK_BOT_TOKEN")
    slack_client = WebClient(token) if token is not None else None

    for log in logs:
        log.action = "ignored"
        db_session.add(log)

        member = db_session.get(Member, log.member_id)
        assert member is not None

        try:
            trello.add_comment_to_card(
                log.card_id,
                f"Member #{member.member_number} {member.firstname} {member.lastname} ignored this task.",
            )
        except Exception as e:
            logger.error(f"Failed to add comment to Trello card {log.card_id}: {e}")

        if slack_client is not None and log.slack_channel_id is not None and log.slack_message_ts is not None:
            try:
                slack_client.chat_update(
                    channel=log.slack_channel_id,
                    ts=log.slack_message_ts,
                    text=f":pleading_face: Marking the task *{log.card_name}* as ignored since we didn't hear from you. We'll try to assign you a different task next time you're at the makerspace.",
                    blocks=[],
                )
            except SlackApiError as e:
                logger.error(f"Failed to update Slack message for ignored task: {e.response['error']}")

        if slack_client is not None and TASK_LOG_CHANNEL is not None:
            try:
                slack_client.chat_postMessage(
                    channel=TASK_LOG_CHANNEL,
                    text=f"Member #{member.member_number} {member.firstname} {member.lastname} ignored the task *{log.card_name}*.",
                )
            except SlackApiError as e:
                logger.error(f"Failed to post to task log channel: {e.response['error']}")

    db_session.commit()


def process_new_visits() -> None:
    """
    Look for new physical_access_log entries and delegate tasks for members who visited.
    Uses a Redis-stored last processed ID to avoid reprocessing.
    """
    last_id = int(redis_connection.get(REDIS_LAST_ID_KEY) or b"0")

    mark_ignored_tasks()

    # Note: we only consider recent visits, since the redis data is ephemeral and may be lost on rebuilds of the container
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
