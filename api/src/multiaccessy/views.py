from datetime import date
from logging import getLogger
from typing import Any, Optional

from dataclasses_json import DataClassJsonMixin
from flask import request
from multiaccessy import service
from service.api_definition import POST, PUBLIC
from service.error import UnprocessableEntity

from .accessy import UUID, AccessyWebhookEventType, accessy_session

logger = getLogger("makeradmin")


class DateTimeWithTimeZone(DataClassJsonMixin):
    dateTime: str
    zoneId: str


class AccessyWebhookEvent(DataClassJsonMixin):
    eventType: AccessyWebhookEventType
    dataData: dict


class AccessyWebhookEventAsset_Operation_Invoked(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    assetOperationId: UUID
    """Universally unique identifier for object."""

    assetPublicationId: UUID
    """Universally unique identifier for object."""

    invokedAt: str
    """A local date time along with time zone."""


class AccessyWebhookEventMembership_Created(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    invitationId: UUID

    role: str
    '''Enum: "ASSET_ADMINISTRATOR" "DELEGATOR" "DEVICE_ADMINISTRATOR" "ORGANIZATION_ADMINISTRATOR" "USER"'''

    requestingUserSuperAdmin: bool


class AccessyWebhookEventMembership_Removed(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    role: str
    '''Enum: "ASSET_ADMINISTRATOR" "DELEGATOR" "DEVICE_ADMINISTRATOR" "ORGANIZATION_ADMINISTRATOR" "USER"'''


class AccessyWebhookEventMembership_Request_Created(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    membershipRequestId: UUID
    """Universally unique identifier for object."""


class AccessyWebhookEventMembership_Request_Approved(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    membershipRequestId: UUID
    """Universally unique identifier for object."""


class AccessyWebhookEventMembership_Request_Denied(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    membershipRequestId: UUID
    """Universally unique identifier for object."""


class AccessyWebhookEventMembership_Role_Added(AccessyWebhookEvent):
    userId: UUID
    """Universally unique identifier for object."""

    organizationId: UUID
    """Universally unique identifier for object."""

    role: str
    '''Enum: "ASSET_ADMINISTRATOR" "DELEGATOR" "DEVICE_ADMINISTRATOR" "ORGANIZATION_ADMINISTRATOR" "USER"'''

    issuedByUserId: UUID
    """Universally unique identifier for object."""


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


def decode_event(data: Any) -> Optional[AccessyWebhookEvent]:
    event_type = AccessyWebhookEventType(data["eventType"])
    if event_type in event_types:
        cls = event_types[event_type]
        return cls.from_dict(data)
    else:
        logger.warning(f"Unknown event type: {event_type}")
        return None


@service.route("/accessy/event", method=POST, permission=PUBLIC)
def accessy_webhook() -> None:
    if accessy_session is None:
        raise UnprocessableEntity("Accessy session not initialized")

    if accessy_session.is_valid_webhook_signature(request.headers["Accessy-Webhook-Signature"]):
        event = decode_event(request.json)
        if event is not None:
            logger.info(f"Received accessy event: {event.to_dict()}")
        return None
    else:
        raise UnprocessableEntity("Invalid signature")
