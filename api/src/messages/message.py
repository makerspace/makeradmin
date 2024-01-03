from os.path import abspath, dirname

from jinja2 import Environment, FileSystemLoader, select_autoescape
from service.config import get_public_url

from messages.models import Message, MessageTemplate

template_loader = FileSystemLoader(abspath(dirname(dirname(__file__))) + "/templates")
template_env = Environment(loader=template_loader, autoescape=select_autoescape())


def render_template(name, **kwargs):
    return template_env.get_template(name).render(**kwargs)


def send_message(template: MessageTemplate, member, db_session=None, recipient_email=None, **kwargs) -> None:
    if recipient_email is None:
        recipient_email = member.email

    subject = render_template(
        f"{template.value}.subject.html",
        public_url=get_public_url,
        member=member,
        **kwargs,
    )

    body = render_template(
        f"{template.value}.body.html",
        public_url=get_public_url,
        member=member,
        **kwargs,
    )

    if not db_session:
        from service.db import db_session

    db_session.add(
        Message(
            subject=subject,
            body=body,
            member_id=member.member_id,
            recipient=recipient_email,
            status=Message.QUEUED,
            template=template.value,
        )
    )
