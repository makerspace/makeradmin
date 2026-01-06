import signal
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html import unescape
from logging import getLogger
from threading import Event
from time import sleep
from typing import Any, Literal, Optional
from urllib.parse import quote_plus

import dispatch_sms
import requests
import serde
from core.auth import create_access_token
from dispatch_sms import send_sms
from membership.membership import get_members_and_membership, get_membership_summaries, get_membership_summary
from membership.models import Member, Span
from messages.message import send_message
from messages.models import Message, MessageTemplate
from multiaccess.label_data import (
    BoxLabel,
    DryingLabel,
    FireSafetyLabel,
    LabelType,
    LabelTypeTagged,
    TemporaryStorageLabel,
)
from multiaccess.memberbooth import get_label_public_url
from multiaccess.models import MemberboothLabelAction
from quiz.models import QuizQuestion, QuizQuestionOption
from quiz.views import QuizMemberStat, quiz_member_answer_stats
from rocky.process import log_exception, stoppable
from service.config import config, get_api_url, get_mysql_config, get_public_url
from service.db import create_mysql_engine, db_session
from shop.models import ProductAction
from shop.shop_data import pending_actions
from shop.transactions import pending_action_value_sum
from sqlalchemy import func, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

logger = getLogger("email-dispatcher")

LABACCESS_REMINDER_DAYS_BEFORE = 20
LABACCESS_REMINDER_GRACE_PERIOD = 28

MEMBERSHIP_REMINDER_DAYS_BEFORE = 20
MEMBERSHIP_REMINDER_GRACE_PERIOD = 28

QUIZ_DAYS_FROM_FIRST_EMAIL_TO_REMINDER = 4
QUIZ_DAYS_BETWEEN_REMINDERS = 21

warned_about_missing_key = False


class NoEmailAuthConfigured(Exception):
    pass


@dataclass
class SendMessage:
    template: MessageTemplate
    member: Member
    recipient: str | None = None
    sms: bool = False
    associated_id: int | None = None
    additional_template_args: dict[str, Any] | None = None


def send_messages(mailgun_key: Optional[str], domain: str, sender: str, to_override: Optional[str], limit: int) -> None:
    query = db_session.query(Message)
    query = query.filter(Message.status == Message.QUEUED)
    query = query.limit(limit)

    skipped_emails = []
    skipped_sms = []

    for message in query:
        to = message.recipient
        msg = f"sending {message.id} to {to}"
        recipient_type = message.recipient_type

        if to_override:
            msg += f" (overriding to {to_override})"
            to = to_override
            recipient_type = "email"

        msg += f": {message.subject}"

        try:
            while True:
                try:
                    if recipient_type == "email":
                        if mailgun_key is None:
                            raise NoEmailAuthConfigured()
                        response = requests.post(
                            f"https://api.mailgun.net/v3/{domain}/messages",
                            auth=("api", mailgun_key),
                            data={
                                "from": sender,
                                "to": to,
                                "subject": message.subject,
                                "html": message.body,
                            },
                        )
                    elif recipient_type == "sms":
                        response = send_sms(to, unescape(message.body))
                    else:
                        assert False, f"unknown recipient type {recipient_type}"
                    break
                except requests.ConnectionError as e:
                    # Can happen if e.g. the mailgun is down for a few seconds (which does happen!)
                    logger.warning(f"Temporary connection error when sending email. Retrying in a few seconds: {e}\n")
                    sleep(5)
        except NoEmailAuthConfigured:
            skipped_emails.append(message)
            continue
        except dispatch_sms.NoAuthConfigured:
            skipped_sms.append(message)
            continue

        logger.info(msg)

        if response.ok:
            message.status = Message.SENT
            message.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)

            db_session.add(message)
            db_session.commit()

        else:
            message.status = Message.FAILED

            db_session.add(message)
            db_session.commit()

            logger.error(f"failed to send {message.id} to {to}: {response.content.decode('utf-8')}")

    if len(skipped_emails) > 0:
        logger.warning(f"Skipped sending {len(skipped_emails)} emails because no Mailgun API key is configured.")
        for message in skipped_emails:
            message.status = Message.FAILED
            db_session.add(message)
        db_session.commit()
    if len(skipped_sms) > 0:
        logger.warning(f"Skipped sending {len(skipped_sms)} SMS because no 46elks authentication is configured.")
        for message in skipped_sms:
            message.status = Message.FAILED
            db_session.add(message)
        db_session.commit()


def already_sent_message(template: MessageTemplate, member_id: int, days: int) -> bool:
    """True if a message has been sent with the given template to the member in the last #days days"""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    reminder_sent = (
        db_session.query(Message)
        .filter(
            Message.member_id == member_id,
            Message.template == template.value,
            now - timedelta(days=days) < Message.created_at,
        )
        .count()
    )
    return reminder_sent > 0


def schedule_messages(messages: list[SendMessage]) -> None:
    for msg in messages:
        send_message(
            template=msg.template,
            member=msg.member,
            db_session=db_session,
            recipient=msg.recipient,
            sms=msg.sms,
            associated_id=msg.associated_id,
            **(msg.additional_template_args or {}),
        )


def memberbooth_labels(
    action_id_filter: int | None = None, observation_send_delay: timedelta | None = None
) -> list[SendMessage]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Define the time window for "recent" as the past two weeks

    recent_window = now - timedelta(days=14)
    messages_to_send: list[SendMessage] = []

    # Organize actions by label and type. More recent of the same type overwrites older ones.
    # label_actions: dict[
    #     int, dict[Literal["observed"] | Literal["reported"] | Literal["cleaned_away"], MemberboothLabelAction | None]
    # ] = defaultdict(lambda: {"observed": None, "reported": None, "cleaned_away": None})
    # for ac in recent_actions:
    #     label_actions[ac.label_id][ac.action] = ac

    # Helper to check if a message was already sent for a label recently
    def already_sent_for_label(template: MessageTemplate, member_id: int, label_id: int) -> bool:
        return (
            db_session.query(Message)
            .filter(
                Message.member_id == member_id,  # Purely a performance optimization
                Message.template == template.value,
                Message.created_at >= recent_window,
            )
            .join(MemberboothLabelAction, MemberboothLabelAction.id == Message.associated_id)
            .filter(MemberboothLabelAction.label_id == label_id)
            .count()
            > 0
        ) or any(
            msg.template == template and msg.member.member_id == member_id and msg.associated_id == label_id
            for msg in messages_to_send
        )

    recent_actions_q = db_session.query(MemberboothLabelAction).filter(
        MemberboothLabelAction.created_at >= recent_window,
        MemberboothLabelAction.action != "observed",
    )

    if action_id_filter is not None:
        recent_actions_q = recent_actions_q.filter(MemberboothLabelAction.id == action_id_filter)

    recent_actions = (
        recent_actions_q.join(
            Message,
            (Message.associated_id == MemberboothLabelAction.id)
            & (
                Message.template.in_(
                    [
                        MessageTemplate.MEMBERBOOTH_LABEL_REPORT.value,
                        MessageTemplate.MEMBERBOOTH_LABEL_CLEANED_AWAY.value,
                        MessageTemplate.MEMBERBOOTH_LABEL_REPORT_SMS.value,
                        MessageTemplate.MEMBERBOOTH_LABEL_CLEANED_AWAY_SMS.value,
                        MessageTemplate.MEMBERBOOTH_BOX_CLEANED_AWAY.value,
                        MessageTemplate.MEMBERBOOTH_BOX_CLEANED_AWAY_SMS.value,
                    ]
                )
            ),
            isouter=True,
        )
        .filter(Message.id.is_(None))  # No message sent yet
        .order_by(MemberboothLabelAction.created_at.asc())
        .all()
    )

    def get_common_kws(label_action: MemberboothLabelAction, member: Member, deserialized_label: LabelType) -> dict:
        membership_summary = get_membership_summary(member.member_id)

        thing_name = "item"
        thing_name_sv = "sak"
        expires_at: date | None = None
        if isinstance(deserialized_label, BoxLabel):
            thing_name = "lab storage box"
            thing_name_sv = "labblåda"
            expires_at = (
                membership_summary.effective_labaccess_end + timedelta(days=45)
                if membership_summary.effective_labaccess_end is not None
                else None
            )
        elif isinstance(deserialized_label, TemporaryStorageLabel):
            desc = deserialized_label.description
            if len(desc) > 33:
                desc = desc[:30] + "..."
            thing_name = f"item with the label '{desc}'"
            thing_name_sv = f"sak med etiketten '{desc}'"
            expires_at = deserialized_label.expires_at
        elif isinstance(deserialized_label, FireSafetyLabel):
            thing_name = f"item in the fire safety cabinett"
            thing_name_sv = f"sak i brandsäkra skåpet"
            expires_at = deserialized_label.expires_at
        elif isinstance(deserialized_label, DryingLabel):
            thing_name = f"item that was left to dry"
            thing_name_sv = f"sak som lämnades för att torka"
            expires_at = deserialized_label.expires_at.date()

        days_after_expiration = (now.date() - expires_at).days if expires_at is not None else None
        days_to_expiration = (expires_at - now.date()).days if expires_at is not None else None

        common_kws: dict[str, Any] = dict(
            label=deserialized_label,
            thing_name=thing_name,
            thing_name_sv=thing_name_sv,
            expires_at=expires_at,
            days_after_expiration=days_after_expiration,
            days_to_expiration=days_to_expiration,
            labaccess_end_date=membership_summary.effective_labaccess_end,
            days_after_labaccess_expiration=(
                (now.date() - membership_summary.effective_labaccess_end).days
                if membership_summary.effective_labaccess_end is not None
                else "∞"
            ),
            label_type=str(type(deserialized_label)),
            label_url=get_label_public_url(label_action.label_id),
            image_url=get_api_url(f"/multiaccess/memberbooth/label_action/{label_action.id}/image")
            if label_action.image
            else None,
        )
        return common_kws

    # Send messages for recent non-observation actions (if not already sent)
    # E.g. if a label was reported or cleaned away.
    for action in recent_actions:
        label = action.label
        deserialized_label: LabelType = serde.from_dict(LabelTypeTagged, label.data)  # type: ignore
        member = db_session.get(Member, label.member_id)
        assert member is not None
        common_kws = get_common_kws(action, member, deserialized_label)

        action_author = db_session.get(Member, action.action_member_id)
        assert action_author is not None, f"action {action.id} has no valid action_member_id {action.action_member_id}"
        # logger.info(
        #     f"Processing label {label_id} with obs={obs}, rep={rep}, clean={clean}, deserialized_label={deserialized_label}"
        # )

        if action.action == "reported":
            for tp, sms in [
                (MessageTemplate.MEMBERBOOTH_LABEL_REPORT, False),
                (MessageTemplate.MEMBERBOOTH_LABEL_REPORT_SMS, True),
            ]:
                logger.info(f"Sending message {tp} for label {label.id} to member {member.member_id}")
                messages_to_send.append(
                    SendMessage(
                        associated_id=action.id,
                        template=tp,
                        member=member,
                        sms=sms,
                        additional_template_args=common_kws
                        | {
                            "action": action,
                            "action_author_name": f"{action_author.firstname} {action_author.lastname}",
                        },
                    )
                )
        elif action.action == "cleaned_away":
            tps = [
                (MessageTemplate.MEMBERBOOTH_LABEL_CLEANED_AWAY, False),
                (MessageTemplate.MEMBERBOOTH_LABEL_CLEANED_AWAY_SMS, True),
            ]
            if isinstance(deserialized_label, BoxLabel):
                tps = [
                    (MessageTemplate.MEMBERBOOTH_BOX_CLEANED_AWAY, False),
                    (MessageTemplate.MEMBERBOOTH_BOX_CLEANED_AWAY_SMS, True),
                ]
            for tp, sms in tps:
                logger.info(f"Sending message {tp} for label {label.id} to member {member.member_id}")
                messages_to_send.append(
                    SendMessage(
                        associated_id=action.id,
                        template=tp,
                        member=member,
                        sms=sms,
                        additional_template_args=common_kws | {"action": action},
                    )
                )
        else:
            assert False, f"unknown action {action.action}"

    # Get all recent actions for observations, reports, and cleanings
    # Get recent observations, but exclude those where a non-observation action (e.g. "reported", "cleaned_away")
    # was taken for the same label within a few days of the observation.
    non_obs_alias = MemberboothLabelAction.__table__.alias("non_obs")

    recent_observations_q = db_session.query(MemberboothLabelAction).filter(
        MemberboothLabelAction.created_at >= recent_window,
        # Don't send messages for very recent observations, to allow time for the member to e.g. report after an observation
        MemberboothLabelAction.created_at < (now - observation_send_delay if observation_send_delay else now),
        MemberboothLabelAction.action == "observed",
        ~db_session.query(non_obs_alias.c.id)
        .filter(
            non_obs_alias.c.label_id == MemberboothLabelAction.label_id,
            non_obs_alias.c.action != "observed",
            non_obs_alias.c.created_at > MemberboothLabelAction.created_at - timedelta(days=1),
            non_obs_alias.c.created_at <= MemberboothLabelAction.created_at + timedelta(days=1),
        )
        .exists(),
    )

    if action_id_filter is not None:
        recent_observations_q = recent_observations_q.filter(MemberboothLabelAction.id == action_id_filter)

    recent_observations = recent_observations_q.order_by(MemberboothLabelAction.created_at.asc()).all()

    # Map label_id to the most recent observation
    observations: dict[int, MemberboothLabelAction] = {}
    for obs in recent_observations:
        observations[obs.label_id] = obs

    # Send messages for recent observations (no recent report/cleaning, and not already sent)
    # For example that a label is about to expire within a few weeks
    for label_id, action in observations.items():
        label = action.label
        deserialized_label: LabelType = serde.from_dict(LabelTypeTagged, label.data)  # type: ignore
        member = db_session.get(Member, label.member_id)
        assert member is not None
        common_kws = get_common_kws(action, member, deserialized_label)
        expires_at = common_kws["expires_at"]
        assert expires_at is None or isinstance(expires_at, date)

        if (
            isinstance(deserialized_label, TemporaryStorageLabel)
            or isinstance(deserialized_label, FireSafetyLabel)
            or isinstance(deserialized_label, BoxLabel)
        ):
            assert expires_at is not None
            if expires_at < now.date() + timedelta(days=14):
                # Expired or about to expire soon
                if expires_at < now.date():
                    # Expired
                    tp = (
                        MessageTemplate.MEMBERBOOTH_BOX_EXPIRED
                        if isinstance(deserialized_label, BoxLabel)
                        else MessageTemplate.MEMBERBOOTH_LABEL_EXPIRED
                    )
                    if not already_sent_for_label(tp, member.member_id, label_id):
                        messages_to_send.append(
                            SendMessage(
                                associated_id=action.id,
                                template=tp,
                                member=member,
                                additional_template_args=common_kws | {"action": action},
                            )
                        )
                else:
                    # About to expire
                    tp = (
                        MessageTemplate.MEMBERBOOTH_BOX_EXPIRING_SOON
                        if isinstance(deserialized_label, BoxLabel)
                        else MessageTemplate.MEMBERBOOTH_LABEL_EXPIRING_SOON
                    )
                    if not already_sent_for_label(tp, member.member_id, label_id):
                        messages_to_send.append(
                            SendMessage(
                                associated_id=action.id,
                                template=tp,
                                member=member,
                                additional_template_args=common_kws | {"action": action},
                            )
                        )

    return messages_to_send


def labaccess_reminder() -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

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
        if already_sent_message(MessageTemplate.LABACCESS_REMINDER, member.member_id, LABACCESS_REMINDER_GRACE_PERIOD):
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
    now = datetime.now(timezone.utc).replace(tzinfo=None).date()

    t0 = time.time()
    member_ids = db_session.scalars(select(Member.member_id).filter(Member.deleted_at == None)).all()

    memberships = get_membership_summaries(member_ids)
    t1 = time.time()
    logger.info(f"get_members_and_membership took {t1 - t0:.2f}s")
    end_date_reminder_target = now + timedelta(days=MEMBERSHIP_REMINDER_DAYS_BEFORE)

    for member_id, membership in zip(member_ids, memberships):
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
        if already_sent_message(MessageTemplate.MEMBERSHIP_REMINDER, member_id, MEMBERSHIP_REMINDER_GRACE_PERIOD):
            continue

        already_purchased = (
            pending_action_value_sum(member_id=member_id, action_type=ProductAction.ADD_MEMBERSHIP_DAYS) > 0
        )

        member = db_session.get_one(Member, member_id)
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
    GET_STARTED_QUIZ_ID = 1
    quiz_id = GET_STARTED_QUIZ_ID
    quiz_members = quiz_member_answer_stats(quiz_id)
    quiz_members_dict = {quiz_member.member_id: quiz_member for quiz_member in quiz_members}
    now = datetime.now(timezone.utc).replace(tzinfo=None)

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

    total_quiz_questions = (
        db_session.scalar(
            select(func.count()).where(QuizQuestion.quiz_id == quiz_id).where(QuizQuestion.deleted_at.is_(None))
        )
        or 0
    )

    for member in members:
        quiz_member = quiz_members_dict.get(member.member_id, None)
        if quiz_member is None:
            quiz_member = QuizMemberStat(
                member_id=member.member_id,
                remaining_questions=total_quiz_questions,
                correctly_answered_questions=0,
                ever_completed=False,
            )

        # Don't bother members who have ever completed the quiz (even if new questions were added later)
        if not quiz_member.ever_completed:
            member_data = id_to_member.get(member.member_id)
            assert member_data is not None
            member, membership = member_data
            # Shouldn't really happen, but best check (db race conditions might cause it I guess)
            if member is None:
                continue

            # We need an email
            if member.email is None or len(member.email) == 0:
                continue

            # Check if the member has any pending purchase of lab access (important to ensure new members get the quiz before the key handout if possible)
            pending_labaccess = member.member_id in members_with_pending_labaccess

            # Only send messages to members whose labaccess is active or pending
            # We don't check effective labaccess, because if a member only has special labaccess,
            # then they are likely either not super involved, or they are not actually a member, but instead a cleaner or similar.
            if not (membership.labaccess_active or pending_labaccess):
                continue

            if member.labaccess_agreement_at is None:
                # Members should get the quiz *after* their introduction
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
                QUIZ_FEATURE_INTRODUCED = datetime(2020, 8, 25)
                is_oldmember = member.created_at < QUIZ_FEATURE_INTRODUCED - timedelta(days=14)
                if is_oldmember:
                    template = MessageTemplate.QUIZ_FIRST_OLDMEMBER
                    # Ignore old members. We don't send the quiz to them right now
                    continue
                else:
                    template = MessageTemplate.QUIZ_FIRST_NEWMEMBER

            url = get_login_link(member, "automatic quiz reminder", f"/member/quiz/{quiz_id}")

            send_message(
                template=template,
                member=member,
                db_session=db_session,
                remaining_questions=quiz_member.remaining_questions,
                correctly_answered_questions=quiz_member.correctly_answered_questions,
                url=url,
            )


def get_login_link(member: Member, browser: str, path: str) -> str:
    redirect = get_public_url(path)
    access_token = create_access_token("localhost", browser, member.member_id, valid_duration=timedelta(days=4))[
        "access_token"
    ]
    return get_public_url(f"/member/login/{access_token}?redirect=" + quote_plus(redirect))


if __name__ == "__main__":
    exit = Event()

    def handle_signal(signum: int, frame: Any) -> None:
        logger.error(f"Got signal {signum}, exiting...")
        exit.set()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, handle_signal)

    with log_exception(status=1), stoppable():
        parser = ArgumentParser(
            description="Dispatch emails in db send queue.", formatter_class=ArgumentDefaultsHelpFormatter
        )

        parser.add_argument("--sleep", default=1, help="Sleep time (in seconds) between doing ant work.")
        parser.add_argument("--limit", default=4, help="Max messages to send every time checking for messages.")

        args = parser.parse_args()

        engine = create_mysql_engine(**get_mysql_config())
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        logger.info(f"checking for emails to send every {args.sleep} seconds, limit is {args.limit}")

        key = config.get("MAILGUN_KEY", log_value=False)
        if key is not None and key.strip() == "":
            key = None

        domain = config.get("MAILGUN_DOMAIN")
        sender = config.get("MAILGUN_FROM")
        to_override = config.get("MAILGUN_TO_OVERRIDE")
        last_reminder_check = 0.0

        # Don't send emails immediately, to avoid clobbering up the logs
        exit.wait(2)

        while not exit.is_set():
            try:
                if time.time() - last_reminder_check > 60 * 60:
                    # These checks are kinda slow (takes a few hundred ms)
                    # so don't do them as often. They are not time critical anyway.
                    last_reminder_check = time.time()
                    logger.info("checking for reminders to send")
                    labaccess_reminder()
                    membership_reminder()
                    quiz_reminders()

                    db_session.commit()

                schedule_messages(memberbooth_labels(observation_send_delay=timedelta(minutes=5)))
                send_messages(key, domain, sender, to_override, args.limit)
                db_session.commit()
            except DatabaseError as e:
                logger.warning(f"failed to do db query. ignoring: {e}")
            finally:
                db_session.remove()

            exit.wait(args.sleep)
