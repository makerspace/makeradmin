from dataclasses import dataclass
from datetime import date, datetime
from logging import getLogger
from typing import Any, Optional

from dataclasses_json import DataClassJsonMixin
from flask import request
from multiaccessy import service
from multiaccessy.models import PhysicalAccessEntry
from service.api_definition import POST, PUBLIC
from service.db import db_session
from service.error import UnprocessableEntity

from .accessy import UUID, AccessyWebhookEventType, accessy_session

logger = getLogger("makeradmin")


class DateTimeWithTimeZone(DataClassJsonMixin):
    dateTime: str
    zoneId: str


@dataclass
class AccessyWebhookEvent(DataClassJsonMixin):
    pass


@dataclass
class AccessyWebhookEventAsset_Operation_Invoked(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    assetOperationId: UUID
    """Universally unique identifier for object."""

    assetPublicationId: UUID
    """Universally unique identifier for object."""

    invokedAt: datetime
    """A local date time along with time zone."""


@dataclass
class AccessyWebhookEventMembership_Created(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    invitationId: UUID

    role: str
    '''Enum: "ASSET_ADMINISTRATOR" "DELEGATOR" "DEVICE_ADMINISTRATOR" "ORGANIZATION_ADMINISTRATOR" "USER"'''

    requestingUserSuperAdmin: bool


@dataclass
class AccessyWebhookEventMembership_Removed(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    role: str
    '''Enum: "ASSET_ADMINISTRATOR" "DELEGATOR" "DEVICE_ADMINISTRATOR" "ORGANIZATION_ADMINISTRATOR" "USER"'''


@dataclass
class AccessyWebhookEventMembership_Request_Created(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    membershipRequestId: UUID
    """Universally unique identifier for object."""


@dataclass
class AccessyWebhookEventMembership_Request_Approved(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    membershipRequestId: UUID
    """Universally unique identifier for object."""


@dataclass
class AccessyWebhookEventMembership_Request_Denied(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    membershipRequestId: UUID
    """Universally unique identifier for object."""


@dataclass
class AccessyWebhookEventMembership_Role_Added(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    role: str
    '''Enum: "ASSET_ADMINISTRATOR" "DELEGATOR" "DEVICE_ADMINISTRATOR" "ORGANIZATION_ADMINISTRATOR" "USER"'''

    issuedByUserId: UUID
    """Universally unique identifier for object."""


@dataclass
class AccessyWebhookEventMembership_Role_Removed(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    # TODO: Incorrect?
    role: UUID
    """Universally unique identifier for object."""

    issuedByUserId: UUID
    """Universally unique identifier for object."""


@dataclass
class AccessyWebhookEventGuestDoorEntry(AccessyWebhookEvent):
    assetOperationId: UUID
    """Universally unique identifier for object."""

    assetOperationName: str
    """Name of the asset operation."""

    entryDateTime: DateTimeWithTimeZone

    value: str

    assetName: str

    assetId: UUID


event_types = {
    AccessyWebhookEventType.ASSET_OPERATION_INVOKED: AccessyWebhookEventAsset_Operation_Invoked,
    # AccessyWebhookEventType.ACCESS_REQUEST: AccessyWebhookEventAccess_Request,
    # AccessyWebhookEventType.APPLICATION_ADDED: AccessyWebhookEventApplication_Added,
    # AccessyWebhookEventType.APPLICATION_REMOVED: AccessyWebhookEventApplication_Removed,
    # AccessyWebhookEventType.GUEST_DOOR_ENTRY: AccessyWebhookEventGuest_Door_Entry,
    AccessyWebhookEventType.MEMBERSHIP_CREATED: AccessyWebhookEventMembership_Created,
    AccessyWebhookEventType.MEMBERSHIP_REMOVED: AccessyWebhookEventMembership_Removed,
    AccessyWebhookEventType.MEMBERSHIP_REQUEST_CREATED: AccessyWebhookEventMembership_Request_Created,
    AccessyWebhookEventType.MEMBERSHIP_REQUEST_APPROVED: AccessyWebhookEventMembership_Request_Approved,
    AccessyWebhookEventType.MEMBERSHIP_REQUEST_DENIED: AccessyWebhookEventMembership_Request_Denied,
    AccessyWebhookEventType.MEMBERSHIP_ROLE_ADDED: AccessyWebhookEventMembership_Role_Added,
    AccessyWebhookEventType.MEMBERSHIP_ROLE_REMOVED: AccessyWebhookEventMembership_Role_Removed,
    # AccessyWebhookEventType.ORGANIZATION_INVITATION_DELETED: AccessyWebhookEventOrganization_Invitation_Deleted,
}


def decode_event(event_type_str: str, data: Any) -> Optional[AccessyWebhookEvent]:
    event_type = AccessyWebhookEventType(event_type_str)
    if event_type in event_types:
        cls = event_types[event_type]
        return cls.from_dict(data)
    else:
        logger.warning(f"Unknown event type: {event_type}")
        return None


def handle_event(event: AccessyWebhookEvent) -> None:
    assert accessy_session is not None

    if isinstance(event, AccessyWebhookEventAsset_Operation_Invoked):
        member_id = accessy_session.get_member_id_from_accessy_id(event.userId)
        if member_id is None:
            logger.warning(f"Accessy user could not be associated with a makerspace member: {event.userId}")

        db_session.add(
            PhysicalAccessEntry(
                member_id=member_id,
                accessy_user_id=event.userId,
                accessy_asset_operation_id=event.assetOperationId,
                accessy_asset_publication_id=event.assetPublicationId,
                invoked_at=event.invokedAt,
            )
        )
        db_session.commit()


@service.route("/event", method=POST, permission=PUBLIC)
def accessy_webhook() -> None:
    if accessy_session is None:
        raise UnprocessableEntity("Accessy session not initialized")

    if accessy_session.is_valid_webhook_signature(request.headers["Accessy-Webhook-Signature"]):
        event = decode_event(request.headers["X-Axs-Event-Type"], request.json)
        if event is not None:
            logger.info(f"Received accessy event: {event.to_dict()}")
            handle_event(event)
        return None
    else:
        raise UnprocessableEntity("Invalid signature")
        raise UnprocessableEntity("Invalid signature")
        raise UnprocessableEntity("Invalid signature")
