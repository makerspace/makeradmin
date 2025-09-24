from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from json.decoder import JSONDecodeError
from logging import getLogger
from typing import Literal

import flask
import serde
import serde.json
from dataclasses_json import DataClassJsonMixin
from flask import Response, g, redirect, request
from membership.member_entity import MemberEntity
from membership.membership import MembershipData, get_membership_summary
from membership.models import Member
from messages.models import Message, MessageTemplate
from messages.views import message_entity
from PIL import Image, ImageOps
from serde.compat import SerdeError
from service.api_definition import (
    DELETE,
    GET,
    MEMBER_EDIT,
    MEMBER_VIEW,
    MEMBERBOOTH,
    MESSAGE_SEND,
    MESSAGE_VIEW,
    POST,
    PUBLIC,
    USER,
    Arg,
    symbol,
)
from service.db import db_session
from service.error import BadRequest, Forbidden, NotFound
from sqlalchemy import select
from werkzeug.wrappers.request import FileStorage

from multiaccess import service, short_url_service
from multiaccess.box_terminator import box_terminator_boxes, box_terminator_nag, box_terminator_validate
from multiaccess.label_data import BoxLabelV1, BoxLabelV2, LabelType, LabelTypeTagged, TemporaryStorageLabelV1
from multiaccess.memberbooth import (
    UploadedLabel,
    create_label,
    get_label_public_url,
    get_label_qr_code_url,
    member_number_to_memberinfo,
    pin_login_to_memberinfo,
    tag_to_memberinfo,
)
from multiaccess.models import MemberboothLabel, MemberboothLabelAction

logger = getLogger("memberbooth")


@service.route("/memberbooth/tag/<string:tagid>", method=GET, permission=MEMBERBOOTH)
def memberbooth_tag(tagid: str) -> dict | None:
    r = tag_to_memberinfo(tagid)
    return r.to_dict() if r else None


@dataclass
class PinLoginRequest(DataClassJsonMixin):
    member_number: int
    pin_code: str


@service.route("/memberbooth/pin-login", method=POST, permission=MEMBERBOOTH)
def memberbooth_pin_login() -> dict:
    request_data = PinLoginRequest.from_dict(request.get_json())
    r = pin_login_to_memberinfo(request_data.member_number, request_data.pin_code)
    return r.to_dict()


@service.route("/memberbooth/member/<string:member_number>", method=GET, permission=MEMBERBOOTH)
def memberbooth_member(member_number: int) -> dict | None:
    r = member_number_to_memberinfo(member_number)
    return r.to_dict() if r else None


@service.route("/memberbooth/label", method=POST, permission=MEMBERBOOTH, status="created")
def memberbooth_post_label() -> dict:
    request_data = request.get_json()
    logger.info(request_data)
    try:
        label = serde.json.from_dict(LabelTypeTagged, request_data)
    except Exception as e:
        label = None
        # Maybe this is an old label format, try to convert it
        for tp in [BoxLabelV2, BoxLabelV1, TemporaryStorageLabelV1]:
            try:
                label = serde.json.from_dict(tp, request_data).migrate()
                if label is None:
                    raise BadRequest("Member not found", status="member_not_found")
                break
            except SerdeError:
                pass
            except JSONDecodeError:
                pass
        if label is None:
            raise BadRequest(f"Failed to deserialize: {request_data}: {e}") from e
    return serde.to_dict(create_label(label))


# Note: All labels are public. This is by design, as they are in any case printed and put on physical objects.
@service.route("/memberbooth/label/<int:id>", method=GET, permission=PUBLIC)
def memberbooth_get_label_route(id: int) -> dict:
    return serde.to_dict(memberbooth_get_label(id))


def memberbooth_get_label(id: int) -> UploadedLabel:
    label_db = db_session.execute(select(MemberboothLabel).where(MemberboothLabel.id == id)).scalar_one_or_none()

    if label_db is None:
        raise NotFound()
    if label_db.deleted_at is not None:
        # If someone accesses this URL, the label is likely not actually gone
        # Treat this as an observation and un-delete the label
        label_db.deleted_at = None
        db_session.add(label_db)
        db_session.flush()

    data_dict: dict = label_db.data  # type: ignore
    label: LabelType = serde.from_dict(LabelTypeTagged, data_dict)  # validate
    return UploadedLabel(
        public_url=get_label_public_url(label.base.id),
        public_observation_url=get_label_qr_code_url(label.base.id),
        label=label,
    )


# Note: All labels are public. This is by design, as they are in any case printed and put on physical objects.
@service.route("/memberbooth/label/<int:id>", method=DELETE, permission=USER)
def memberbooth_delete_label(id: int) -> Response:
    label = db_session.execute(
        select(MemberboothLabel).where(MemberboothLabel.id == id, MemberboothLabel.deleted_at.is_(None))
    ).scalar_one_or_none()

    if label is None:
        raise NotFound()

    if label.member_id != g.user_id:
        raise Forbidden("Only the label owner may delete it")

    label.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.flush()
    return Response(status=204)


@service.route("/memberbooth/label/<int:id>/message", method=GET, permission=USER)
def memberbooth_label_related_messages(id: int) -> list[dict]:
    label = db_session.execute(select(MemberboothLabel).where(MemberboothLabel.id == id)).scalar_one_or_none()

    if label is None:
        raise NotFound()

    label_message_types = [
        MessageTemplate.MEMBERBOOTH_LABEL_REPORT,
        MessageTemplate.MEMBERBOOTH_LABEL_CLEANED_AWAY,
        MessageTemplate.MEMBERBOOTH_LABEL_REPORT_SMS,
        MessageTemplate.MEMBERBOOTH_LABEL_CLEANED_AWAY_SMS,
        MessageTemplate.MEMBERBOOTH_BOX_CLEANED_AWAY,
        MessageTemplate.MEMBERBOOTH_BOX_CLEANED_AWAY_SMS,
        MessageTemplate.MEMBERBOOTH_LABEL_EXPIRED,
        MessageTemplate.MEMBERBOOTH_LABEL_EXPIRING_SOON,
        MessageTemplate.MEMBERBOOTH_BOX_EXPIRED,
        MessageTemplate.MEMBERBOOTH_BOX_EXPIRING_SOON,
    ]

    q = (
        select(Message)
        .join(MemberboothLabelAction, MemberboothLabelAction.id == Message.associated_id)
        .where(
            Message.template.in_([v.value for v in label_message_types]),
            MemberboothLabelAction.label_id == id,
        )
        .order_by(Message.created_at.desc())
    )

    if MESSAGE_VIEW not in g.permissions:
        # Only allow access to messages to the member themselves
        q = q.where(Message.member_id == g.user_id)

    messages = db_session.execute(q).scalars().all()

    return [message_entity.to_obj(message) for message in messages]


@serde.serde
class LabelActionResponse:
    id: int
    label: UploadedLabel


# This route is used by QR codes on labels. Scanning one should automatically register an observation, and then redirect to the public label URL.
@short_url_service.route("/<int:id>", method=GET, permission=PUBLIC)
def memberbooth_label_qrcode(id: int) -> Response:
    try:
        memberbooth_label_action(id, action="observed")
    except NotFound:
        # If the label does not exist, we still want to redirect to the public URL
        pass
    return flask.make_response(redirect(get_label_public_url(id), code=302))


@service.route("/memberbooth/label/<int:id>/membership", method=GET, permission=MEMBER_VIEW)
def memberbooth_membership_by_label(id: int) -> dict:
    label = db_session.execute(select(MemberboothLabel).where(MemberboothLabel.id == id)).scalar_one_or_none()

    if label is None:
        raise NotFound()

    membership = get_membership_summary(label.member_id)

    return membership.to_dict()


@service.route("/memberbooth/label/<int:id>/observe", method=POST, permission=PUBLIC, status="created")
def memberbooth_observe_label(id: int) -> dict:
    return memberbooth_label_action(
        id, action="observed", message=request.form.get("message"), image=request.files.get("image")
    )


@service.route("/memberbooth/label/<int:id>/report", method=POST, permission=MESSAGE_SEND, status="created")
def memberbooth_report_label(id: int) -> dict:
    return memberbooth_label_action(
        id, action="reported", message=request.form.get("message"), image=request.files.get("image")
    )


@service.route("/memberbooth/label/<int:id>/terminate", method=POST, permission=MESSAGE_SEND, status="created")
def memberbooth_terminate_label(id: int) -> dict:
    return memberbooth_label_action(
        id, action="cleaned_away", message=request.form.get("message"), image=request.files.get("image")
    )


def memberbooth_label_action(
    id: int,
    action: Literal["reported"] | Literal["cleaned_away"] | Literal["observed"],
    message: str | None = None,
    image: FileStorage | None = None,
) -> dict:
    if not message and action == "reported":
        raise BadRequest("Message is required when reporting.")

    label = db_session.execute(select(MemberboothLabel).where(MemberboothLabel.id == id)).scalar_one_or_none()

    if label is None:
        raise NotFound()
    if label.deleted_at is not None:
        # A report, observation or cleaning means that the label still exists
        # So if it had been deleted, un-delete it
        label.deleted_at = None
        db_session.add(label)
        db_session.flush()

    if image:
        img = image.read()
        img_io = BytesIO(img)
        with Image.open(img_io) as im:
            # Correct and bake in orientation based on EXIF data
            im = ImageOps.exif_transpose(im)
            # Resize image to at most 1000 pixels in width or height to avoid taking up too much space.
            im.thumbnail((1000, 1000), Image.Resampling.BILINEAR)
            out_io = BytesIO()
            im.save(out_io, format="webp")
            img = out_io.getvalue()
    else:
        img = None

    db_action = MemberboothLabelAction(
        label_id=id,
        action_member_id=g.user_id,
        session_token=g.session_token,
        action=action,
        message=message,
        image=img,
    )

    # Remove previous action of the same type for this label within the last 5 minutes.
    # This avoids putting e.g. multiple observations in the database if someone scans the QR code multiple times.
    # This is not strictly necessary to handle (the emailing code already deduplicates emails), but it keeps the database cleaner.
    five_minutes_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
    prev_action = (
        db_session.execute(
            select(MemberboothLabelAction)
            .where(
                MemberboothLabelAction.label_id == id,
                MemberboothLabelAction.action == action,
                MemberboothLabelAction.created_at >= five_minutes_ago,
                MemberboothLabelAction.action_member_id == g.user_id,
            )
            .order_by(MemberboothLabelAction.created_at.desc())
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if prev_action:
        if message is None and img is None:
            # If the previous action is identical, or has more info than this one, just return the old one
            # This is the common case for observations
            return serde.to_dict(
                LabelActionResponse(id=prev_action.id, label=memberbooth_get_label(prev_action.label_id))
            )

        db_session.delete(prev_action)

    db_session.add(db_action)
    db_session.flush()

    return serde.to_dict(LabelActionResponse(id=db_action.id, label=memberbooth_get_label(db_action.label_id)))


# Links to these images are included in emails sent out to members, so they need to be public.
@service.route("/memberbooth/label_action/<int:id>/image", method=GET, permission=PUBLIC)
def memberbooth_label_action_image(id: int) -> Response:
    action = db_session.execute(
        select(MemberboothLabelAction).where(MemberboothLabelAction.id == id)
    ).scalar_one_or_none()

    if action is None:
        raise NotFound()
    if action.image is None:
        raise NotFound()

    return Response(action.image, mimetype="image/webp")


@service.route("/box-terminator/boxes", method=GET, permission=MEMBER_EDIT)
def box_terminator_boxes_routes():
    """Returns a list of all boxes scanned, ever."""
    return box_terminator_boxes()


@service.route("/box-terminator/nag", method=POST, permission=MEMBER_EDIT)
def box_terminator_nag_route(member_number=Arg(int), box_label_id=Arg(int), nag_type=Arg(symbol)):
    """Send a nag email for this box."""
    return box_terminator_nag(member_number, box_label_id, nag_type)


@service.route("/box-terminator/validate-box", method=POST, permission=MEMBER_EDIT)
def box_terminator_validate_route(member_number=Arg(int), box_label_id=Arg(int)):
    """Used when scanning boxes."""
    return box_terminator_validate(member_number, box_label_id, g.session_token)
