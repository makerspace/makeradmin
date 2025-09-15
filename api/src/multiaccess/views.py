from datetime import datetime, timezone
from logging import getLogger

import serde
import serde.json
from flask import g, request
from service.api_definition import DELETE, GET, MEMBER_EDIT, MEMBERBOOTH, POST, PUBLIC, USER, Arg, symbol
from service.db import db_session
from service.error import BadRequest, Forbidden, NotFound
from sqlalchemy import select

from multiaccess import service
from multiaccess.box_terminator import box_terminator_boxes, box_terminator_nag, box_terminator_validate
from multiaccess.labal_data import LabelType
from multiaccess.memberbooth import (
    LabelWrapper,
    UploadedLabel,
    UploadLabelRequest,
    create_label,
    get_label_public_url,
    member_number_to_memberinfo,
    pin_login_to_memberinfo,
    tag_to_memberinfo,
)
from multiaccess.models import MemberboothLabel

logger = getLogger("memberbooth")


@service.route("/memberbooth/tag", method=GET, permission=MEMBERBOOTH)
def memberbooth_tag(tagid: str = Arg(str)) -> dict | None:
    r = tag_to_memberinfo(tagid)
    return r.to_dict() if r else None


@service.route("/memberbooth/pin-login", method=GET, permission=MEMBERBOOTH)
def memberbooth_pin_login(member_number: int = Arg(int), pin_code: str = Arg(str)) -> dict:
    r = pin_login_to_memberinfo(member_number, pin_code)
    return r.to_dict()


@service.route("/memberbooth/member", method=GET, permission=MEMBERBOOTH)
def memberbooth_member(member_number: int = Arg(int)) -> dict | None:
    r = member_number_to_memberinfo(member_number)
    return r.to_dict() if r else None


@service.route("/memberbooth/label", method=POST, permission=MEMBERBOOTH)
def memberbooth_post_label() -> dict:
    request_data = request.get_json()
    logger.info(request_data)
    logger.info(type(request_data))
    try:
        data = serde.json.from_json(UploadLabelRequest, request_data)
    except Exception as e:
        raise BadRequest(f"Failed to deserialize: {request_data}: {e}") from e
    return serde.to_dict(create_label(data))


# Note: All labels are public. This is by design, as they are in any case printed and put on physical objects.
@service.route("/memberbooth/label/<int:id>", method=GET, permission=PUBLIC)
def memberbooth_get_label(id: int) -> dict:
    label = db_session.execute(select(MemberboothLabel).where(MemberboothLabel.id == id)).scalar_one_or_none()

    if label is None:
        raise NotFound()
    if label.deleted_at is not None:
        # If someone accesses this URL, the label is likely not actually gone
        # Treat this as an observation and un-delete the label
        label.deleted_at = None
        db_session.add(label)
        db_session.flush()

    data_dict: dict = label.data  # type: ignore
    data = LabelWrapper.from_dict(data_dict)  # validate

    return serde.to_dict(UploadedLabel(public_url=get_label_public_url(label.id), label=data.label))


# Note: All labels are public. This is by design, as they are in any case printed and put on physical objects.
@service.route("/memberbooth/label/<int:id>", method=DELETE, permission=USER)
def memberbooth_delete_label(id: int) -> None:
    label = db_session.execute(
        select(MemberboothLabel).where(MemberboothLabel.id == id, MemberboothLabel.deleted_at.is_(None))
    ).scalar_one_or_none()

    if label is None:
        raise NotFound()

    if label.member_id != g.user_id:
        raise Forbidden("Only the label owner may delete it")

    label.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.flush()


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
