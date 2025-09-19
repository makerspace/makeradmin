from html import unescape
from os.path import abspath, dirname
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from membership.models import Member
from service.config import get_public_url

from messages.models import Message, MessageTemplate

template_loader = FileSystemLoader(abspath(dirname(dirname(__file__))) + "/templates")
template_env = Environment(loader=template_loader, autoescape=select_autoescape())


def render_template(name: str, **kwargs: Any) -> str:
    return template_env.get_template(name).render(**kwargs)


def send_message(
    template: MessageTemplate,
    member: Member,
    db_session: Any = None,
    recipient: str | None = None,
    *,
    sms: bool = False,
    associated_id: int | None = None,
    **kwargs: Any,
) -> None:
    recipient_type = "sms" if sms else "email"
    if recipient is None:
        recipient = member.phone if sms else member.email

    subject = (
        render_template(
            f"{template.value}.subject.html",
            public_url=get_public_url,
            member=member,
            **kwargs,
        )
        if not sms
        else ""
    )
    if subject:
        subject = unescape(subject)

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
            recipient=recipient,
            recipient_type=recipient_type,
            status=Message.QUEUED,
            template=template.value,
            associated_id=associated_id,
        )
    )
