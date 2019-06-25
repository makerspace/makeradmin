from flask import render_template

from messages.models import MessageTemplate, Message
from service.config import get_public_url
from service.db import db_session as service_db_session


def send_message(template: MessageTemplate, member, db_session=None, **kwargs):
    
    subject = render_template(
        f"{template.value}.subject.jinja2",
        public_url=get_public_url,
        member=member,
        **kwargs,
    )
    
    body = render_template(
        f"{template.value}.body.jinja2",
        public_url=get_public_url,
        member=member,
        **kwargs,
    )
    
    session = db_session or service_db_session
    
    session.add(Message(
        subject=subject,
        body=body,
        member_id=member.member_id,
        recipient=member.email,
        status=Message.QUEUED,
        template=template.value,
    ))

