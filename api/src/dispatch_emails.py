import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from contextlib import closing
from datetime import datetime, timedelta, timezone
from os.path import abspath, dirname
from time import sleep
from urllib.parse import quote_plus

import requests
from core.auth import create_access_token
from jinja2 import Environment, FileSystemLoader, select_autoescape
from membership.membership import get_members_and_membership
from membership.models import Member, Span
from messages.message import send_message
from messages.models import Message, MessageTemplate
from quiz.views import quiz_member_answer_stats
from rocky.process import log_exception, stoppable
from service.config import config, get_mysql_config, get_public_url
from service.db import create_mysql_engine, db_session
from service.logging import logger
from shop.models import ProductAction
from shop.shop_data import pending_actions
from shop.transactions import pending_action_value_sum
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

LABACCESS_REMINDER_DAYS_BEFORE = 20
LABACCESS_REMINDER_GRACE_PERIOD = 28

MEMBERSHIP_REMINDER_DAYS_BEFORE = 20
MEMBERSHIP_REMINDER_GRACE_PERIOD = 28

QUIZ_DAYS_FROM_FIRST_EMAIL_TO_REMINDER = 4
QUIZ_DAYS_BETWEEN_REMINDERS = 21


def send_messages(key, domain, sender, to_override, limit):
    query = db_session.query(Message)
    query = query.filter(Message.status == Message.QUEUED)
    query = query.limit(limit)

    for message in query:
        to = message.recipient
        msg = f"sending {message.id} to {to}"

        if to_override:
            msg += f" (overriding to {to_override})"
            to = to_override

        msg += f": {message.subject}"

        logger.info(msg)

        while True:
            try:
                response = requests.post(
                    f"https://api.mailgun.net/v3/{domain}/messages",
                    auth=("api", key),
                    data={
                        "from": sender,
                        "to": to,
                        "subject": message.subject,
                        "html": message.body,
                    },
                )
                break
            except requests.ConnectionError as e:
                # Can happen if e.g. the mailgun is down for a few seconds (which does happen!)
                logger.warning(f"Temporary connection error when sending email. Retrying in a few seconds: {e}\n")
                sleep(5)

        if response.ok:
            message.status = Message.SENT
            message.sent_at = datetime.now(timezone.utc)

            db_session.add(message)
            db_session.commit()

        else:
            message.status = Message.FAILED

            db_session.add(message)
            db_session.commit()

            logger.error(f"failed to send {message.id} to {to}: {response.content.decode('utf-8')}")


def already_sent_message(template: MessageTemplate, member: Member, days: int):
    """True if a message has been sent with the given template to the member in the last #days days"""
    now = datetime.now(timezone.utc)
    reminder_sent = (
        db_session.query(Message)
        .filter(
            Message.member == member,
            Message.template == template.value,
            now - timedelta(days=days) < Message.created_at,
        )
        .count()
    )
    return reminder_sent > 0


def labaccess_reminder() -> None:
    now = datetime.now(timezone.utc)

    end_date_reminder_target = now.date() + timedelta(days=LABACCESS_REMINDER_DAYS_BEFORE)

    query = db_session.query(Member)
    query = query.join(Span)
    query = query.filter(
        Member.deleted_at.is_(None),
        Span.type == Span.LABACCESS,
        Span.deleted_at.is_(None),
        Span.enddate == end_date_reminder_target,
    )

    for member in query:
        # We have a candidate, now check if we should send a reminder.

        # First double check the end date so we don't send reminder if there is another span further in the future.
        end_date = (
            db_session.query(func.max(Span.enddate))
            .filter(Span.member == member, Span.type == Span.LABACCESS, Span.deleted_at.is_(None))
            .scalar()
        )
        if end_date != end_date_reminder_target:
            continue

        # Don't send a reminder if we sent a reminder the last 28 days.
        if already_sent_message(MessageTemplate.LABACCESS_REMINDER, member, LABACCESS_REMINDER_GRACE_PERIOD):
            continue

        already_purchased = (
            pending_action_value_sum(member_id=member.member_id, action_type=ProductAction.ADD_LABACCESS_DAYS) > 0
        )

        # If the member has a subscription, don't send a reminder, as it will be renewed automatically.
        # TODO: Ideally we should have a cron job that checks if the subscription is truly valid on the stripe side as well,
        # and in that case nulls the subscription id on the makeradmin side.
        # It *shouldn't* (TM) get out of sync. But it is theoretically possible that that it does, and then the member
        # would loose access without us reminding them (bad).
        already_purchased |= member.stripe_labaccess_subscription_id is not None

        if already_purchased:
            continue

        logger.info(f"sending labaccess reminder to member with id {member.member_id}")

        send_message(
            template=MessageTemplate.LABACCESS_REMINDER,
            member=member,
            db_session=db_session,
            expiration_date=end_date,
        )


def membership_reminder() -> None:
    now = datetime.now(timezone.utc).date()

    members, memberships = get_members_and_membership()
    members = list(members)
    end_date_reminder_target = now + timedelta(days=MEMBERSHIP_REMINDER_DAYS_BEFORE)

    for member, membership in zip(members, memberships):
        if membership.membership_end is None:
            # Not a member
            continue

        if membership.membership_end < now and not membership.effective_labaccess_active:
            # Membership already expired
            # If the member has labaccess active then the member has likely forgot to renew the yearly membership.
            # Having a yearly membership is a requirement for being allowed to purchase lab membership.
            continue

        if membership.membership_end > end_date_reminder_target:
            # Membership is valid for a long time
            continue

        # Don't send a reminder if we sent a reminder the last 28 days.
        if already_sent_message(MessageTemplate.MEMBERSHIP_REMINDER, member, MEMBERSHIP_REMINDER_GRACE_PERIOD):
            continue

        already_purchased = (
            pending_action_value_sum(member_id=member.member_id, action_type=ProductAction.ADD_MEMBERSHIP_DAYS) > 0
        )

        already_purchased |= member.stripe_membership_subscription_id is not None

        if already_purchased:
            # Member has already purchased extra membership
            continue

        url = get_login_link(member, "membership reminder", "/shop")

        send_message(
            template=MessageTemplate.MEMBERSHIP_REMINDER,
            member=member,
            url=url,
            db_session=db_session,
            expiration_date=membership.membership_end,
        )

        logger.info(
            f"sending yearly membership reminder to member with id {member.member_id}. Expires "
            + str(membership.membership_end)
        )


def quiz_reminders() -> None:
    # Assume quiz 1 is the get started quiz
    quiz_id = 1
    quiz_members = quiz_member_answer_stats(quiz_id)
    now = datetime.now(timezone.utc)

    members, memberships = get_members_and_membership()
    id_to_member = {member.member_id: (member, membership) for member, membership in zip(members, memberships)}

    # Get all pending shop actions and check which members have pending purchases of lab access
    actions = pending_actions()
    members_with_pending_labaccess = set()
    for action in actions:
        if action["action"]["action"] == "add_labaccess_days" and action["action"]["value"] > 0:
            members_with_pending_labaccess.add(action["member_id"])

    recently_sent_messages_by_member = set(
        x[0]
        for x in db_session.query(Message.member_id)
        .filter(
            (
                (Message.template == MessageTemplate.QUIZ_FIRST_NEWMEMBER.value)
                & (now - timedelta(days=QUIZ_DAYS_FROM_FIRST_EMAIL_TO_REMINDER) < Message.created_at)
            )
            | (
                (Message.template == MessageTemplate.QUIZ_FIRST_OLDMEMBER.value)
                & (now - timedelta(days=QUIZ_DAYS_FROM_FIRST_EMAIL_TO_REMINDER) < Message.created_at)
            )
            | (
                (Message.template == MessageTemplate.QUIZ_REMINDER.value)
                & (now - timedelta(days=QUIZ_DAYS_BETWEEN_REMINDERS) < Message.created_at)
            )
        )
        .group_by(Message.member_id)
        .all()
    )

    sent_first_message_by_member = set(
        x[0]
        for x in db_session.query(Message.member_id)
        .filter(
            (Message.template == MessageTemplate.QUIZ_FIRST_NEWMEMBER.value)
            | (Message.template == MessageTemplate.QUIZ_FIRST_OLDMEMBER.value)
        )
        .group_by(Message.member_id)
        .all()
    )

    for quiz_member in quiz_members:
        if quiz_member.remaining_questions > 0:
            member, membership = id_to_member.get(quiz_member.member_id)
            # Shouldn't really happen, but best check (db race conditions might cause it I guess)
            if member is None:
                continue

            # We need an email
            if member.email is None or len(member.email) == 0:
                continue

            # Check if the member has any pending purchase of lab access (important to ensure new members get the quiz before the key handout if possible)
            pending_labaccess = member.member_id in members_with_pending_labaccess

            # Only send messages to members whose labaccess is active or pending
            if not (membership.effective_labaccess_active or pending_labaccess):
                continue

            # Check if a message has already been sent within given time periods
            if member.member_id in recently_sent_messages_by_member:
                continue

            firstmessage_sent = member.member_id in sent_first_message_by_member

            template = MessageTemplate.QUIZ_REMINDER
            if not firstmessage_sent:
                # An old member has been member for more than 30 days.
                # The oldmember template was used when the quiz was first introduced to give
                # existing members a customized message.
                # It also applies to those who haven't been members for a long time and become members again.
                is_oldmember = member.created_at < now - timedelta(days=14)
                if is_oldmember:
                    template = MessageTemplate.QUIZ_FIRST_OLDMEMBER
                    # Ignore old members. We don't send the quiz to them right now
                    continue
                else:
                    template = MessageTemplate.QUIZ_FIRST_NEWMEMBER

            url = get_login_link(member, "automatic quiz reminder", "/member/quiz/1")

            send_message(
                template=template,
                member=member,
                db_session=db_session,
                remaining_questions=quiz_member.remaining_questions,
                correctly_answered_questions=quiz_member.correctly_answered_questions,
                url=url,
            )


def get_login_link(member, browser, path):
    redirect = get_public_url(path)
    access_token = create_access_token("localhost", browser, member.member_id, valid_duration=timedelta(days=4))[
        "access_token"
    ]
    return get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))


if __name__ == "__main__":
    with log_exception(status=1), stoppable():
        parser = ArgumentParser(
            description="Dispatch emails in db send queue.", formatter_class=ArgumentDefaultsHelpFormatter
        )

        parser.add_argument("--sleep", default=4, help="Sleep time (in seconds) between doing ant work.")
        parser.add_argument("--limit", default=10, help="Max messages to send every time checking for messages.")

        args = parser.parse_args()

        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        logger.info(f"checking for emails to send every {args.sleep} seconds, limit is {args.limit}")

        key = config.get("MAILGUN_KEY", log_value=False)
        domain = config.get("MAILGUN_DOMAIN")
        sender = config.get("MAILGUN_FROM")
        to_override = config.get("MAILGUN_TO_OVERRIDE")
        last_quiz_check = time.time()

        while True:
            sleep(args.sleep)
            try:
                labaccess_reminder()
                membership_reminder()
                if time.time() - last_quiz_check > 20:
                    # This check is kinda slow (takes maybe 100 ms)
                    # so don't do it as often. It's not time critical anyway.
                    last_quiz_check = time.time()
                    quiz_reminders()
                db_session.commit()
                send_messages(key, domain, sender, to_override, args.limit)
                db_session.commit()
            except DatabaseError as e:
                logger.warning(f"failed to do db query. ignoring: {e}")
            finally:
                db_session.remove()
