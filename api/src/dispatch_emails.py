from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from contextlib import closing
from datetime import datetime, timedelta
from os.path import abspath, dirname
from time import sleep
import time
from urllib.parse import quote_plus

import requests
from jinja2 import Environment, select_autoescape, FileSystemLoader
from rocky.process import log_exception, stoppable
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

from membership.models import Member, Span
from membership.membership import get_members_and_membership
from messages.message import send_message
from messages.models import Message, MessageTemplate
from service.config import get_mysql_config, config, get_public_url
from service.db import create_mysql_engine, db_session
from service.logging import logger
from shop.models import ProductAction
from shop.transactions import pending_action_value_sum
from quiz.views import quiz_member_answer_stats
from core.auth import create_access_token

template_loader = FileSystemLoader(abspath(dirname(__file__)) + '/templates')
template_env = Environment(loader=template_loader, autoescape=select_autoescape())


LABACCESS_REMINDER_DAYS_BEFORE = 20
LABACCESS_REMINDER_GRACE_PERIOD = 28

QUIZ_DAYS_FROM_FIRST_EMAIL_TO_REMINDER = 4
QUIZ_DAYS_BETWEEN_REMINDERS = 21

def render_template(name, **kwargs):
    return template_env.get_template(name).render(**kwargs)


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

        response = requests.post(f"https://api.mailgun.net/v3/{domain}/messages", auth=('api', key),
                                 data={
                                     'from': sender,
                                     'to': to,
                                     'subject': message.subject,
                                     'html': message.body,
                                 })

        if response.ok:
            message.status = Message.SENT
            message.sent_at = datetime.utcnow()

            db_session.add(message)
            db_session.commit()

        else:
            message.status = Message.FAILED

            db_session.add(message)
            db_session.commit()

            logger.error(f"failed to send {message.id} to {to}: {response.content.decode('utf-8')}")


def already_sent_message(template: MessageTemplate, member: Member, days: int):
    ''' True if a message has been sent with the given template to the member in the last #days days'''
    now = datetime.utcnow()
    reminder_sent = db_session.query(Message).filter(
        Message.member == member,
        Message.template == template.value,
        now - timedelta(days=days) < Message.created_at,
    ).count()
    return reminder_sent > 0

def labaccess_reminder(render_template):
    now = datetime.utcnow()

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
        end_date = db_session.query(func.max(Span.enddate)).filter(
            Span.member == member,
            Span.type == Span.LABACCESS,
            Span.deleted_at.is_(None)
        ).scalar()
        if end_date != end_date_reminder_target:
            continue

        # Don't send a reminder if we sent a reminder the last 28 days.
        if already_sent_message(MessageTemplate.LABACCESS_REMINDER, member, LABACCESS_REMINDER_GRACE_PERIOD):
            continue

        already_purchased = \
            pending_action_value_sum(member_id=member.member_id, action_type=ProductAction.ADD_LABACCESS_DAYS) > 0
        if already_purchased:
            continue

        logger.info(f'sending labaccess reminder to member with id {member.member_id}')

        send_message(
            template=MessageTemplate.LABACCESS_REMINDER,
            member=member,
            db_session=db_session,
            render_template=render_template,
            expiration_date=end_date,
        )

def quiz_reminders():
    quiz_members = quiz_member_answer_stats()
    now = datetime.utcnow()

    logger.info("Checking quiz reminders")
    members, memberships = get_members_and_membership()
    id_to_member = {
        member.member_id: (member, membership) for member, membership in zip(members, memberships)
    }

    for quiz_member in quiz_members:
        if quiz_member.remaining_questions > 0:
            member, membership = id_to_member.get(quiz_member.member_id)
            # Shouldn't really happen, but best check (db race conditions might cause it I guess)
            if member is None:
                continue

            # We need an email
            if member.email is None or len(member.email) == 0:
                continue

            # Only send messages to members whose labaccess is active
            if not membership.labaccess_active:
                continue

            if member.email not in ["ronjaharletun@hotmail.com", "aron.granberg@gmail.com", "tbbw82@gmail.com", "leila_el@hotmail.com", "lina.ottosson93@gmail.com", "erasmus.cedernaes@gmail.com", "makerspace.se@cj.se", "oskarstrid01@gmail.com", "farouk.hashim@Gmail.com", "lundquist.andreas@gmail.com", "info@erikcederberg.se"]:
                continue

            sent_newmember = already_sent_message(MessageTemplate.QUIZ_FIRST_NEWMEMBER, member, QUIZ_DAYS_FROM_FIRST_EMAIL_TO_REMINDER)
            sent_oldmember = already_sent_message(MessageTemplate.QUIZ_FIRST_OLDMEMBER, member, QUIZ_DAYS_FROM_FIRST_EMAIL_TO_REMINDER)
            sent_reminder = already_sent_message(MessageTemplate.QUIZ_REMINDER, member, QUIZ_DAYS_BETWEEN_REMINDERS)

            if sent_newmember or sent_oldmember or sent_reminder:
                continue

            firstmessage_sent = db_session.query(Message).filter(
                Message.member == member,
                (Message.template == MessageTemplate.QUIZ_FIRST_OLDMEMBER.value) | (Message.template == MessageTemplate.QUIZ_FIRST_NEWMEMBER.value)
            ).count() > 0

            template = MessageTemplate.QUIZ_REMINDER
            if not firstmessage_sent:
                # An old member has been member for more than 30 days.
                # The oldmember template was used when the quiz was first introduced to give
                # existing members a customized message.
                # It also applies to those who haven't been members for a long time and become members again.
                is_oldmember = member.created_at < now - timedelta(days=30)
                if is_oldmember:
                    template = MessageTemplate.QUIZ_FIRST_OLDMEMBER
                else:
                    template = MessageTemplate.QUIZ_FIRST_NEWMEMBER

            redirect = get_public_url(f"/member/quiz")
            # Allow a very long login token for the quiz
            # It's not like this is a security risk, having access to someones email will automatically allow one to login anyway.
            access_token = create_access_token("localhost", "automatic quiz reminder", member.member_id, valid_duration=timedelta(days=2))['access_token']
            url = get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))

            send_message(
                template=template,
                member=member,
                db_session=db_session,
                render_template=render_template,
                remaining_questions=quiz_member.remaining_questions,
                correctly_answered_questions=quiz_member.correctly_answered_questions,
                url=url,
            )

    logger.info("Done")

if __name__ == '__main__':

    with log_exception(status=1), stoppable():
        parser = ArgumentParser(description="Dispatch emails in db send queue.",
                                formatter_class=ArgumentDefaultsHelpFormatter)

        parser.add_argument('--sleep', default=4, help='Sleep time (in seconds) between doing ant work.')
        parser.add_argument('--limit', default=10, help='Max messages to send every time checking for messages.')

        args = parser.parse_args()

        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        logger.info(f'checking for emails to send every {args.sleep} seconds, limit is {args.limit}')

        key = config.get('MAILGUN_KEY', log_value=False)
        domain = config.get('MAILGUN_DOMAIN')
        sender = config.get('MAILGUN_FROM')
        to_override = config.get('MAILGUN_TO_OVERRIDE')
        last_quiz_check = time.time()

        while True:
            sleep(args.sleep)
            try:
                labaccess_reminder(render_template)
                if time.time() - last_quiz_check > 30:
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
