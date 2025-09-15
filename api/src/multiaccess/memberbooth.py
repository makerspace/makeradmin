from dataclasses import dataclass
from logging import getLogger

import serde
from dataclasses_json import DataClassJsonMixin
from membership.member_auth import verify_password
from membership.membership import MembershipData, get_membership_summary
from membership.models import Key, Member
from serde import InternalTagging
from service.config import get_public_url
from service.db import db_session
from service.error import NotFound

from multiaccess.labal_data import LabelType
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
    membership_data: MembershipData


@serde.serde(tagging=InternalTagging("type"))
class UploadedLabel:
    public_url: str
    label: LabelType


@serde.serde(tagging=InternalTagging("type"))
class UploadLabelRequest:
    label: LabelType


def memberbooth_response_object(member: Member, membership_data: MembershipData) -> MemberboothMemberInfo:
    return MemberboothMemberInfo(
        member_id=member.member_id,
        member_number=member.member_number,
        firstname=member.firstname,
        lastname=member.lastname,
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
    return memberbooth_response_object(key.member, membership_data)


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
    return memberbooth_response_object(member, membership_data)


def member_number_to_memberinfo(member_number: int) -> MemberboothMemberInfo | None:
    member = db_session.query(Member).filter(Member.member_number == member_number, Member.deleted_at.is_(None)).first()

    if not member:
        return None

    membership_data = get_membership_summary(member.member_id)
    return memberbooth_response_object(member, membership_data)


def get_label_public_url(label_id: int) -> str:
    return get_public_url("/label/") + str(label_id)


@serde.serde(tagging=InternalTagging("type"))
class LabelWrapper:
    label: LabelType

    @staticmethod
    def from_dict(value: dict) -> "LabelWrapper":
        value = {"label": value}  # wrap, to handle unions properly
        data = serde.from_dict(LabelWrapper, value)
        return data

    def to_dict(self) -> dict:
        label_data = serde.to_dict(self)
        label_data = label_data["label"]  # unwrap
        return label_data


def create_label(data: UploadLabelRequest) -> UploadedLabel:
    member = (
        db_session.query(Member)
        .filter(Member.member_number == data.label.base.member_number, Member.deleted_at.is_(None))
        .first()
    )
    if not member:
        raise NotFound(f"Member with number {data.label.base.member_number} not found.")

    db_label = MemberboothLabel(
        id=data.label.base.id,
        member_id=member.member_id,
        data=LabelWrapper(label=data.label).to_dict(),
    )
    db_session.add(db_label)
    db_session.flush()
    return UploadedLabel(public_url=get_label_public_url(db_label.id), label=data.label)


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
    for label in labels:
        data_dict: dict = label.data  # type: ignore
        data = LabelWrapper.from_dict(data_dict)  # validate
        result.append(UploadedLabel(public_url=get_label_public_url(label.id), label=data.label))

    return result
