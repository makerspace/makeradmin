from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Optional

import requests
from membership.models import Member
from service.config import config, get_mysql_config
from service.db import create_mysql_engine, db_session
from slack_sdk import WebClient
from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker
from trello.trello import (
    SOURCE_LIST_NAME,
    TRELLO_API_BASE,
    _auth_params,
    cached_cards,
    delete_card,
    get_list_id_by_name,
    refresh_cache,
)

from tasks.delegate import (
    TASK_LOG_CHANNEL,
    CardCompletionInfo,
    CardRequirements,
    SlackChannel,
    SlackInteraction,
    SlackInteractionAction,
    SlackMessage,
    SlackUser,
    delegate_task_for_member,
)
from tasks.models import TaskDelegationLog, TaskSize
from tasks.views import slack_handle_task_feedback


@dataclass
class CLIArgs:
    command: str
    member_number: Optional[int] = None
    allow: Optional[list[str]] = None
    all: Optional[bool] = None
    task_id: Optional[int] = None
    task_name: Optional[str] = None
    done: Optional[bool] = None
    ignore: Optional[bool] = None
    other: Optional[bool] = None
    refresh: Optional[bool] = None


# def delete_available_tasks_with_templates() -> None:
#     """
#     Delete all cards in the PRIMARY_SOURCE_LIST that have a template card associated with them.
#     """
#     # Get the list ID for "Available Tasks"
#     available_tasks_list_id = get_list_id_by_name(PRIMARY_SOURCE_LIST_NAME)
#     if not available_tasks_list_id:
#         raise RuntimeError("Could not find 'Available Tasks' list on Trello board")

#     # Get all cards in the "Available Tasks" list
#     available_cards = cached_cards(PRIMARY_SOURCE_LIST_NAME)
#     if not available_cards:
#         print("No cards found in 'Available Tasks'.")
#         return

#     # Get all template cards
#     template_cards = cached_cards(TEMPLATE_LIST_NAME)
#     if not template_cards:
#         print("No template cards found.")
#         return

#     # Build a map of template card IDs for quick lookup
#     template_card_ids = {card.id for card in template_cards}

#     print(f"Deleting cards in '{PRIMARY_SOURCE_LIST_NAME}' that have associated template cards...")

#     for card in available_cards:
#         # Use CardCompletionInfo to check if the card is associated with a template card
#         completion_info = CardCompletionInfo.from_card(card, template_cards)
#         if completion_info.template_card_id in template_card_ids:
#             try:
#                 delete_card(card.id)
#                 print(f"Deleted card '{card.name}' (ID: {card.id}).")
#             except Exception as e:
#                 print(f"Failed to delete card '{card.name}' (ID: {card.id}). Error: {e}")


# def make_task_available() -> None:
#     """
#     Make tasks available by copying template cards to the 'Available Tasks' list.
#     """
#     # Archive completed tasks first
#     # delete_available_tasks_with_templates()

#     # Get the list ID for "Available Tasks"
#     available_tasks_list_id = get_list_id_by_name(PRIMARY_SOURCE_LIST_NAME)
#     if not available_tasks_list_id:
#         raise RuntimeError("Could not find 'Available Tasks' list on Trello board")

#     # Get all template cards
#     template_cards = cached_cards(TEMPLATE_LIST_NAME)
#     if not template_cards:
#         print("No template cards found.")
#         return

#     print(f"Found {len(template_cards)} template cards. Copying them to '{PRIMARY_SOURCE_LIST_NAME}'...")

#     for card in template_cards:
#         url = f"{TRELLO_API_BASE}/cards"
#         params = {
#             "idList": available_tasks_list_id,
#             "idCardSource": card.id,
#             **_auth_params(),
#         }
#         response = requests.post(url, params=params, timeout=10)
#         if response.status_code == 200:
#             print(f"Copied template card '{card.name}' to '{PRIMARY_SOURCE_LIST_NAME}'.")
#         else:
#             print(f"Failed to copy template card '{card.name}'. Error: {response.text}")


def main() -> None:
    engine = create_mysql_engine(**get_mysql_config())  # type: ignore
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    parser = ArgumentParser(description="Task delegation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_allow_arg(subparser: ArgumentParser) -> None:
        subparser.add_argument("--allow", nargs="*", default=[], help="List of reasons to ignore when delegating tasks")

    # Delegate command
    delegate_parser = subparsers.add_parser("delegate", help="Delegate a task for a member")
    delegate_parser.add_argument("member_number", type=int, help="Member number to delegate task for")
    delegate_parser.add_argument("--task-name", type=str, help="Name of the task to delegate")
    add_allow_arg(delegate_parser)

    reset_parser = subparsers.add_parser("reset-member", help="Reset task delegation state for a member")
    reset_parser.add_argument("member_number", type=int, help="Member number to delegate task for")

    # Make-task-available command
    # make_task_parser = subparsers.add_parser("make-task-available", help="Make tasks available")
    # make_task_parser.add_argument("--all", action="store_true", help="Make all tasks available")

    # Task command
    task_parser = subparsers.add_parser("task", help="Manage a specific task")
    add_allow_arg(task_parser)
    selector_group = task_parser.add_mutually_exclusive_group(required=True)
    selector_group.add_argument(
        "--task-id",
        type=int,
        help="Task ID to manage.",
    )
    selector_group.add_argument(
        "--task-name",
        type=str,
        help="Task name to manage. The last assigned task will be used, or a new entry will be created if this task is not assigned to anyone right now.",
    )
    selector_group.add_argument(
        "--member-number",
        type=int,
        help="Member to manage. The last assigned task will be used.",
    )
    task_status_group = task_parser.add_mutually_exclusive_group()
    task_status_group.add_argument("--done", action="store_true", help="Mark task as done")
    task_status_group.add_argument("--ignore", action="store_true", help="Ignore the task")
    task_status_group.add_argument("--other", action="store_true", help="Mark task as other")
    task_status_group.add_argument("--refresh", action="store_true", help="Refresh the task")

    args = parser.parse_args()
    cli_args = CLIArgs(
        command=args.command,
        member_number=getattr(args, "member_number", None),
        allow=getattr(args, "allow", None),
        all=getattr(args, "all", None),
        task_id=getattr(args, "task_id", None),
        task_name=getattr(args, "task_name", None),
        done=getattr(args, "done", None),
        ignore=getattr(args, "ignore", None),
        other=getattr(args, "other", None),
        refresh=getattr(args, "refresh", None),
    )

    if cli_args.command == "delegate":
        assert cli_args.member_number is not None
        member = db_session.execute(select(Member).where(Member.member_number == cli_args.member_number)).scalar_one()
        card = None
        if cli_args.task_name is not None:
            refresh_cache()
            cards = cached_cards(SOURCE_LIST_NAME)
            matching_cards = [card for card in cards if card.name == cli_args.task_name]
            if not matching_cards:
                raise RuntimeError(f"No task found with name '{cli_args.task_name}'")
            elif len(matching_cards) > 1:
                raise RuntimeError(f"Multiple tasks found with name '{cli_args.task_name}'")
            card = matching_cards[0]
        delegate_task_for_member(member.member_id, force=True, ignore_reasons=cli_args.allow or [], picked_card=card)
    # elif cli_args.command == "make-task-available":
    #     make_task_available()
    elif cli_args.command == "reset-member":
        assert cli_args.member_number is not None
        member = db_session.execute(select(Member).where(Member.member_number == cli_args.member_number)).scalar_one()

        db_session.execute(delete(TaskDelegationLog).where(TaskDelegationLog.member_id == member.member_id))
        print(f"Reset task delegation state for member #{member.member_number} {member.firstname} {member.lastname}.")
    elif cli_args.command == "task":
        if cli_args.member_number is not None:
            member = db_session.execute(
                select(Member).where(Member.member_number == cli_args.member_number)
            ).scalar_one()

            log = db_session.execute(
                select(TaskDelegationLog)
                .where(TaskDelegationLog.member_id == member.member_id)
                .order_by(TaskDelegationLog.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            if log is None:
                raise RuntimeError(f"No task delegation log found for member #{member.member_number}")
        elif cli_args.task_id is not None:
            log = db_session.execute(
                select(TaskDelegationLog).where(TaskDelegationLog.id == cli_args.task_id)
            ).scalar_one_or_none()
            if log is None:
                raise RuntimeError(f"No task found with ID '{cli_args.task_id}'")
        elif cli_args.task_name is not None:
            log = db_session.execute(
                select(TaskDelegationLog)
                .where(TaskDelegationLog.card_name == cli_args.task_name, TaskDelegationLog.action == "assigned")
                .order_by(TaskDelegationLog.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()

            if log is None:
                cards = cached_cards(SOURCE_LIST_NAME)
                matching_cards = [card for card in cards if card.name == cli_args.task_name]
                if not matching_cards:
                    raise RuntimeError(f"No task found with name '{cli_args.task_name}'")
                elif len(matching_cards) > 1:
                    raise RuntimeError(f"Multiple tasks found with name '{cli_args.task_name}'")
                card = matching_cards[0]
                requirements = CardRequirements.from_card(card)

                if cli_args.done:
                    log = TaskDelegationLog(
                        member_id=None,
                        card_id=card.id,
                        task_size=requirements.size,
                        slack_channel_id=None,
                        slack_message_ts=None,
                        card_name=card.name,
                        action="completed",
                        details="Manually completed via CLI",
                    )
                    db_session.add(log)
                    db_session.commit()

                    if TASK_LOG_CHANNEL is not None:
                        slack_client = WebClient(token=config.get("SLACK_BOT_TOKEN"))
                        slack_client.chat_postMessage(
                            channel=TASK_LOG_CHANNEL,
                            text=f":white_check_mark: <https://trello.com/c/{card.id}|{log.card_name}> was marked as completed manually.",
                        )
                else:
                    raise RuntimeError(
                        f"Task '{cli_args.task_name}' is not currently assigned to any member. If you want to mark it as done manually, use --done."
                    )

                return
        else:
            raise RuntimeError("Either member_number or task_id must be specified for 'task' command")

        assert log.slack_channel_id is not None
        assert log.slack_message_ts is not None

        slack_interaction = SlackInteraction(
            actions=[],
            channel=SlackChannel(id=log.slack_channel_id),
            message=SlackMessage(ts=log.slack_message_ts),
            user=SlackUser(id="<not set>"),
            trigger_id="",
        )

        if cli_args.done:
            action = SlackInteractionAction(action_id="task_feedback_done", value="done")
        elif cli_args.ignore:
            action = SlackInteractionAction(action_id="task_feedback_not_done", value="ignore")
        elif cli_args.other:
            action = SlackInteractionAction(action_id="task_feedback_not_done", value="other")
        elif cli_args.refresh:
            action = SlackInteractionAction(action_id="task_feedback_new_task", value="new_task")
        else:
            raise RuntimeError("No action specified for task command")
        slack_interaction.actions.append(action)

        slack_handle_task_feedback(slack_interaction, ignore_reasons=cli_args.allow or [])

    db_session.commit()


if __name__ == "__main__":
    main()
