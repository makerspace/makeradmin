from flask import render_template

from messages.models import MessageTemplate, Message
from service.config import get_public_url
from service.db import db_session


def send_message(template: MessageTemplate, member, **kwargs):
    
    subject = render_template(
        f"{template.value}_subject.jinja2",
        public_url=get_public_url,
        member=member,
        **kwargs,
    )
    
    body = render_template(
        f"{template.value}_body.jinja2",
        public_url=get_public_url,
        member=member,
        **kwargs,
    )
    
    db_session.add(Message(
        subject=subject,
        body=body,
        member_id=member.member_id,
        recipient=member.email,
        status=Message.QUEUED,
        template=template.value,
    ))

