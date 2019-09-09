from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from contextlib import closing
from datetime import datetime, timedelta
from os.path import abspath, dirname
from time import sleep

import requests
from jinja2 import Environment, select_autoescape, FileSystemLoader
from rocky.process import log_exception, stoppable
from sqlalchemy import func
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

from membership.models import Member, Span
from messages.message import send_message
from messages.models import Message, MessageTemplate
from service.config import get_mysql_config, config
from service.db import create_mysql_engine
from service.logging import logger
from shop.models import ProductAction
from shop.transactions import pending_action_value_sum

template_loader = FileSystemLoader(abspath(dirname(__file__)) + '/templates')
template_env = Environment(loader=template_loader, autoescape=select_autoescape())


LABACCESS_REMINDER_DAYS_BEFORE = 20
LABACCESS_REMINDER_GRACE_PERIOD = 28


def render_template(name, **kwargs):
    return template_env.get_template(name).render(**kwargs)


def send_messages(db_session, key, domain, sender, to_override, limit):
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
            
            logger.error(f"failed to send {message.id} to {to}: {response.content}")


def labaccess_reminder(db_session, render_template):
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
        reminder_sent = db_session.query(Message).filter(
            Message.member == member,
            Message.template == MessageTemplate.LABACCESS_REMINDER.value,
            now - timedelta(days=LABACCESS_REMINDER_GRACE_PERIOD) < Message.created_at,
        ).count()
        if reminder_sent:
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

    db_session.commit()
    

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
        
        while True:
            sleep(args.sleep)
            with closing(session_factory()) as db_session:
                try:
                    labaccess_reminder(db_session, render_template)
                    send_messages(db_session, key, domain, sender, to_override, args.limit)
                except DatabaseError as e:
                    logger.warning(f"failed to do db query. ignoring: {e}")
