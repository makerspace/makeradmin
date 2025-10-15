from dataclasses import dataclass
from logging import getLogger
from urllib.parse import urlparse, urlunparse

import serde
from dataclasses_json import DataClassJsonMixin
from membership.member_auth import get_member_permissions, verify_password
from membership.membership import MembershipData, get_membership_summary
from membership.models import Key, Member
from serde import InternalTagging
from service.config import get_api_url, get_public_url
from service.db import db_session
from service.error import NotFound

from multiaccess.label_data import LabelType, LabelTypeTagged
from multiaccess.models import MemberboothLabel

logger = getLogger("makeradmin")


@dataclass
class MemberboothKeyInfo(DataClassJsonMixin):
    key_id: int
    rfid_tag: str | None


@dataclass
class MemberboothMemberInfo(DataClassJsonMixin):
    member_id: int
    member_number: int
    firstname: str
    lastname: str | None
    keys: list[MemberboothKeyInfo]
    permissions: list[str]
    membership_data: MembershipData


@serde.serde(deny_unknown_fields=True, tagging=InternalTagging("type"))
class UploadedLabel:
    # Public url that can be used to view the given label
    public_url: str
    # Public url that will register an observation of the label, and then redirect to public_url. Used for QR codes.
    public_observation_url: str
    label: LabelType


def memberbooth_response_object(
    member: Member, membership_data: MembershipData, permissions: list[str]
) -> MemberboothMemberInfo:
    return MemberboothMemberInfo(
        member_id=member.member_id,
        member_number=member.member_number,
        firstname=member.firstname,
        lastname=member.lastname,
        permissions=permissions,
        keys=[MemberboothKeyInfo(key_id=key.key_id, rfid_tag=key.tagid) for key in member.keys],
        membership_data=membership_data,
    )


def tag_to_memberinfo(tagid: str) -> MemberboothMemberInfo | None:
    key = (
        db_session.query(Key)
        .join(Key.member)
        .filter(Key.tagid == tagid)
        .filter(
            Member.deleted_at.is_(None),
            Key.deleted_at.is_(None),
        )
        .first()
    )

    if key is None:
        return None

    membership_data = get_membership_summary(key.member_id)

    permissions = [p[1] for p in get_member_permissions(key.member_id)]
    return memberbooth_response_object(key.member, membership_data, permissions)


def pin_login_to_memberinfo(member_number: int, pin_code_or_password: str) -> MemberboothMemberInfo:
    member = (
        db_session.query(Member)
        .filter(Member.member_number == member_number)
        .filter(Member.deleted_at.is_(None))
        .first()
    )

    if member is None:
        logger.info("The member number did not match any known member")
        raise NotFound(f"The member + pin code combination does not belong to any known user.")

    if member.pin_code is None and member.password is None:
        logger.info(f"Member #{member.member_number} has not set a PIN code or password yet")
        raise NotFound(f"The member + pin code/password combination does not belong to any known user.")

    if verify_password(pin_code_or_password, member.password) or member.pin_code == pin_code_or_password:
        # Good, password matched
        pass
    else:
        logger.warning(f"Incorrect PIN code or password for member #{member.member_number}")
        raise NotFound(f"The member + pin code/password combination does not belong to any known user.")

    membership_data = get_membership_summary(member.member_id)
    permissions = [p[1] for p in get_member_permissions(member.member_id)]
    return memberbooth_response_object(member, membership_data, permissions)


def member_number_to_memberinfo(member_number: int) -> MemberboothMemberInfo | None:
    member = db_session.query(Member).filter(Member.member_number == member_number, Member.deleted_at.is_(None)).first()

    if not member:
        return None

    membership_data = get_membership_summary(member.member_id)
    permissions = [p[1] for p in get_member_permissions(member.member_id)]
    return memberbooth_response_object(member, membership_data, permissions)


def get_label_public_url(label_id: int) -> str:
    return get_public_url("/label/") + str(label_id)


def get_label_qr_code_url(label_id: int) -> str:
    # Use short URL service for QR codes, to make them easier to scan.
    # The host and protocol can always be made uppercase, and we make sure to handle an uppercase path too.
    # QR codes encode uppercase alphanumeric characters with fewer bits.
    url = get_api_url(f"/L/{label_id}")
    parsed = urlparse(url)
    # Uppercase scheme and netloc
    new_url = urlunparse(
        (
            # Uppercase scheme and netloc, as they are case-insensitive
            # Also replace HTTPS with HTTP. There will be a redirect to HTTPS anyway, using fewer
            # characters means we can get away with a smaller QR code.
            parsed.scheme.upper().replace("HTTPS", "HTTP"),
            parsed.netloc.upper(),
            parsed.path,  # Note: makeradmin may be hosted in a subdirectory, so we cannot necessarily uppercase the whole path
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
    return new_url


def create_label(label: LabelType) -> UploadedLabel:
    member = (
        db_session.query(Member)
        .filter(Member.member_number == label.base.member_number, Member.deleted_at.is_(None))
        .first()
    )
    if not member:
        raise NotFound(f"Member with number {label.base.member_number} not found.")

    db_label = MemberboothLabel(
        id=label.base.id,
        member_id=member.member_id,
        data=serde.to_dict(label, LabelTypeTagged),  # type: ignore
    )
    db_session.add(db_label)
    db_session.flush()
    return UploadedLabel(
        public_url=get_label_public_url(db_label.id),
        public_observation_url=get_label_qr_code_url(db_label.id),
        label=label,
    )


def get_member_labels(member_id: int) -> list[UploadedLabel]:
    member = db_session.get(Member, member_id)
    if not member:
        raise NotFound(f"Member with id {member_id} not found.")

    labels = (
        db_session.query(MemberboothLabel)
        .filter(MemberboothLabel.member_id == member_id, MemberboothLabel.deleted_at.is_(None))
        .order_by(MemberboothLabel.created_at.desc())
        .all()
    )

    result = []
    for label_db in labels:
        data_dict: dict = label_db.data  # type: ignore
        label: LabelType = serde.from_dict(LabelTypeTagged, data_dict)  # validate
        result.append(
            UploadedLabel(
                public_url=get_label_public_url(label_db.id),
                public_observation_url=get_label_qr_code_url(label_db.id),
                label=label,
            )
        )

    return result
