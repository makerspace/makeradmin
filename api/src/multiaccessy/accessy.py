import json as libjson
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from logging import getLogger
from random import random
from time import sleep
from typing import Any, List, Optional, Union
from urllib.parse import urlparse

import requests
from dataclasses_json import DataClassJsonMixin
from membership.models import Member
from NamedAtomicLock import NamedAtomicLock
from service.config import config
from service.db import db_session
from service.entity import fromisoformat

logger = getLogger("accessy")


class AccessyError(RuntimeError):
    pass


PHONE = str
UUID = str  # The UUID used by Accessy is a 16 byte hexadecimal number formatted as 01234567-abcd-abcd-abcd-0123456789ab (i.e. grouped by 4, 2, 2, 2, 6 with dashes in between)
MSISDN = str  # Standardized number of the form +46123123456

ACCESSY_URL: str = config.get("ACCESSY_URL")
ACCESSY_CLIENT_SECRET: str = config.get("ACCESSY_CLIENT_SECRET", log_value=False)
ACCESSY_CLIENT_ID: str = config.get("ACCESSY_CLIENT_ID")
ACCESSY_LABACCESS_GROUP: str = config.get("ACCESSY_LABACCESS_GROUP")
ACCESSY_SPECIAL_LABACCESS_GROUP: str = config.get("ACCESSY_SPECIAL_LABACCESS_GROUP")
ACCESSY_DO_MODIFY: bool = config.get("ACCESSY_DO_MODIFY", default="false").lower() == "true"


def request(
    method: str,
    path: str,
    token: Optional[str] = None,
    json: dict[str, Any] | DataClassJsonMixin | None = None,
    max_tries: int = 8,
    err_msg: Optional[str] = None,
) -> Any:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json:
        headers["Content-Type"] = "application/json"

    if isinstance(json, DataClassJsonMixin):
        data = json.to_json()
    else:
        data = libjson.dumps(json)

    backoff = 1.0
    for i in range(max_tries):
        response = requests.request(method, ACCESSY_URL + path, data=data, headers=headers)
        if response.status_code == 429:
            logger.warning(
                f"requesting accessy returned 429, too many requests, try {i+1}/{max_tries}, retrying in {backoff}s, {path=}"
            )
            sleep(backoff)
            backoff = backoff * (1.2 + 0.1 * random())
            continue

        if not response.ok:
            msg = f"got an error in the response for {response.request.path_url}, {response.status_code=}: {err_msg or ''}"
            logger.error(msg)
            raise AccessyError(msg)

        try:
            return response.json()
        except ValueError as e:
            if not response.content:
                return {}
            raise e

    raise AccessyError("too many requests")


class AccessyWebhookEventType(Enum):
    ASSET_OPERATION_INVOKED = "ASSET_OPERATION_INVOKED"
    ACCESS_REQUEST = "ACCESS_REQUEST"
    APPLICATION_ADDED = "APPLICATION_ADDED"
    APPLICATION_REMOVED = "APPLICATION_REMOVED"
    GUEST_DOOR_ENTRY = "GUEST_DOOR_ENTRY"
    MEMBERSHIP_CREATED = "MEMBERSHIP_CREATED"
    MEMBERSHIP_REMOVED = "MEMBERSHIP_REMOVED"
    MEMBERSHIP_REQUEST_CREATED = "MEMBERSHIP_REQUEST_CREATED"
    MEMBERSHIP_REQUEST_APPROVED = "MEMBERSHIP_REQUEST_APPROVED"
    MEMBERSHIP_REQUEST_DENIED = "MEMBERSHIP_REQUEST_DENIED"
    MEMBERSHIP_ROLE_ADDED = "MEMBERSHIP_ROLE_ADDED"
    MEMBERSHIP_ROLE_REMOVED = "MEMBERSHIP_ROLE_REMOVED"
    ORGANIZATION_INVITATION_DELETED = "ORGANIZATION_INVITATION_DELETED"

    # Note: Only these seem to have any documentation
    # ASSET_OPERATION_INVOKED
    # MEMBERSHIP_CREATED
    # MEMBERSHIP_REMOVED
    # MEMBERSHIP_REQUEST_CREATED
    # MEMBERSHIP_REQUEST_APPROVED
    # MEMBERSHIP_REQUEST_DENIED
    # MEMBERSHIP_ROLE_ADDED
    # MEMBERSHIP_ROLE_REMOVED
    # GUEST_DOOR_ENTRY


@dataclass
class AccessyWebhookEventTypeObject(DataClassJsonMixin):
    id: int
    name: AccessyWebhookEventType
    group: str


@dataclass
class AccessyMember:
    user_id: Union[UUID, None] = None
    # Get information below later
    phone: Union[str, None] = None
    membership_id: Union[UUID, None] = field(default=None)
    name: str = "<name>"
    member_id: Union[int, None] = None  # Makeradmin member_id
    member_number: Union[int, None] = None  # Makeradmin member_number
    groups: set[str] = field(default_factory=set)

    def __repr__(self) -> str:
        groups = []
        if ACCESSY_LABACCESS_GROUP in self.groups:
            groups.append("labaccess")
        if ACCESSY_SPECIAL_LABACCESS_GROUP in self.groups:
            groups.append("special")
        return f"AccessyMember(phone={self.phone}, name={self.name}, {groups=}, member_id={self.member_id}, member_number={self.member_number}, user_id={self.user_id})"


@dataclass
class AccessyWebhook(DataClassJsonMixin):
    id: UUID
    """An unique id."""

    name: str
    """Name or identifier."""

    signature: str
    """The signature whe webhook will send in the header (Accessy-Webhook-Signature) that can be used to verify it is comming from the correct service (security)."""

    destinationUrl: str
    """The destination url to the webhook, needs to be a https and start with https://"""

    createdAt: str
    """A date when the webhook was created using UTC and the format YYYY-MM-ddTHH:MM.SS.ssssssZ e.g 2021-04-09T09:06:12.627917Z"""

    createdBy: UUID
    """UUID of the user that created this webhook."""

    updatedAt: str
    """A date when the webhook was created using UTC and the format YYYY-MM-ddTHH:MM.SS.ssssssZ e.g 2021-04-09T09:06:12.627917Z"""

    updatedBy: UUID
    """UUID of the user that updated this webhook."""

    eventTypes: list[AccessyWebhookEventTypeObject]
    """An array of event types (one or more) that this webhook should listen to."""


@dataclass
class AccessyWebhookCreate(DataClassJsonMixin):
    name: str
    description: str
    destinationUrl: str
    eventTypes: list[AccessyWebhookEventType]


@dataclass
class AccessyUser(DataClassJsonMixin):
    id: UUID
    firstName: str
    lastName: str
    # uiLanguageCode: str # Ignore, since even though Accessy says it is required, it is not always returned by the API.
    application: bool
    msisdn: Optional[MSISDN] = None


class AccessySession:
    def __init__(self) -> None:
        self.session_token: str | None = None
        self.session_token_token_expires_at: datetime | None = None
        self._organization_id: str | None = None
        self._mutex = threading.Lock()
        self._all_webhooks: Optional[List[AccessyWebhook]] = None
        self._accessy_id_to_member_id_cache: dict[str, int] = {}

    #################
    # Class methods
    #################

    @staticmethod
    def is_env_configured() -> bool:
        return all(
            isinstance(config_var, bool) or (isinstance(config_var, str) and len(config_var) > 0)
            for config_var in (
                ACCESSY_URL,
                ACCESSY_CLIENT_SECRET,
                ACCESSY_CLIENT_ID,
                ACCESSY_LABACCESS_GROUP,
                ACCESSY_SPECIAL_LABACCESS_GROUP,
                ACCESSY_DO_MODIFY,
            )
        )

    #################
    # Public methods
    #################

    def get_member_id_from_accessy_id(self, accessy_id: UUID) -> Optional[int]:
        if accessy_id in self._accessy_id_to_member_id_cache:
            return self._accessy_id_to_member_id_cache[accessy_id]

        user_details = self.get_user_details(accessy_id)

        member = db_session.query(Member).filter(Member.phone == user_details.msisdn).first()
        if member is not None:
            self._accessy_id_to_member_id_cache[accessy_id] = member.member_id
            return member.member_id
        else:
            return None

    def get_all_members(self) -> list[AccessyMember]:
        """Get a list of all Accessy members in the ORG with GROUPS (lab and special)"""

        org_member_ids = set(item["id"] for item in self._get_users_org())

        members = self._user_ids_to_accessy_members(org_member_ids)

        lab_ids = set(item["userId"] for item in self._get_users_lab())
        special_ids = set(item["userId"] for item in self._get_users_special())

        for m in members:
            if m.user_id in lab_ids:
                m.groups.add(ACCESSY_LABACCESS_GROUP)
            if m.user_id in special_ids:
                m.groups.add(ACCESSY_SPECIAL_LABACCESS_GROUP)

        return members

    def is_in_org(self, phone_number: MSISDN, users_org: list[dict] | None = None) -> bool:
        """Check if a user with a specific phone number is in the ORG"""
        if not self.has_authentication():
            return False

        user = self._get_org_user_from_phone(phone_number, users_org)
        if user is not None:
            return True
        return False

    def is_in_group(self, phone_number: MSISDN, access_group_id: UUID) -> bool:
        """Check if a user is in a specific access group"""
        if not self.has_authentication():
            return False

        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return False

        membership_ids = self._get_membership_ids_in_group(access_group_id)
        for id_ in membership_ids:
            if id_ == accessy_member.membership_id:
                return True
        return False

    def remove_from_org(self, member: AccessyMember) -> None:
        self.__delete(f"/org/admin/organization/{self.organization_id()}/user/{member.user_id}")

    def remove_from_group(self, member: AccessyMember, access_group_id: UUID) -> None:
        self.__delete(f"/asset/admin/access-permission-group/{access_group_id}/membership/{member.membership_id}")

    def add_phone_to_group(self, phone_number: MSISDN, access_group_id: UUID) -> None:
        """Add a specific user with phone number to access group"""
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            self.invite_phone_to_org_and_groups([phone_number], [access_group_id])
        else:
            self.add_to_group(accessy_member, access_group_id)

    def add_to_group(self, member: AccessyMember, access_group_id: UUID) -> None:
        self.__put(
            f"/asset/admin/access-permission-group/{access_group_id}/membership",
            json=dict(membership=member.membership_id),
        )

    def invite_phone_to_org_and_groups(
        self, phone_numbers: Iterable[MSISDN], access_group_ids: Iterable[UUID] = [], message_to_user: str = ""
    ) -> None:
        """Invite a list of phone numbers to a list of groups"""
        self.__post(
            f"/org/admin/organization/{self.organization_id()}/invitation",
            json=dict(
                accessPermissionGroupIds=list(access_group_ids), message=message_to_user, msisdns=list(phone_numbers)
            ),
            err_msg=f"invite {phone_numbers=} to org and groups {access_group_ids}. {message_to_user=}",
        )

    def has_authentication(self) -> bool:
        return ACCESSY_CLIENT_ID is not None and ACCESSY_CLIENT_SECRET is not None

    def get_pending_invitations(self, after_date: Optional[date] = None) -> Iterable[MSISDN]:
        """Get all pending invitations after a specific date (including)."""
        if not self.has_authentication():
            return set()

        data = self._get(f"/org/admin/organization/{self.organization_id()}/invitation")
        pending_invitations = set()
        for inv in data:
            recipient = inv["recipientMsisdn"]
            invitation_date = fromisoformat(inv["createdAt"]).date()
            is_pending = inv["status"] == "PENDING"

            if is_pending and (after_date is None or invitation_date >= after_date):
                pending_invitations.add(recipient)
        return pending_invitations

    def organization_id(self) -> str:
        if self._organization_id:
            return self._organization_id
        self.__ensure_token()
        assert self._organization_id is not None
        return self._organization_id

    def get_user_groups(self, phone_number: MSISDN) -> list[str]:
        """Get all of the groups of a member"""
        if not self.has_authentication():
            return []

        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return []

        org_groups = (d["id"] for d in self._get_organization_groups())

        group_descriptions = []
        for group_id in org_groups:
            membership_ids = self._get_membership_ids_in_group(group_id)
            if accessy_member.membership_id in membership_ids:
                group_descriptions.append(self._get_group_description(group_id))

        return group_descriptions

    ################################################
    # Internal methods
    ################################################

    def __ensure_token(self) -> None:
        if not self.has_authentication():
            return

        with self._mutex:  # Only allow one concurrent token refresh as rate limiting on this endpoint is aggressive.
            if (
                not self.session_token
                or self.session_token_token_expires_at is None
                or datetime.now() > self.session_token_token_expires_at
            ):
                now = datetime.now()
                data = request(
                    "post",
                    "/auth/oauth/token",
                    json={
                        "audience": ACCESSY_URL,
                        "grant_type": "client_credentials",
                        "client_id": ACCESSY_CLIENT_ID,
                        "client_secret": ACCESSY_CLIENT_SECRET,
                    },
                )

                self.session_token = data["access_token"]
                self.session_token_token_expires_at = now + timedelta(milliseconds=int(data["expires_in"]))
                logger.info(
                    f"accessy session token refreshed, expires_at={self.session_token_token_expires_at.isoformat()} token={self.session_token}"
                )

            if not self._organization_id:
                data = request(
                    "get",
                    "/asset/user/organization-membership",
                    token=self.session_token,
                )

                match len(data):
                    case 0:
                        raise AccessyError("The API key does not have a corresponding organization membership")
                    case l if l > 1:
                        logger.warning("API key has several memberships. This is probably an error...")

                self._organization_id = data[0]["organizationId"]
                logger.info(f"fetched accessy organization_id {self._organization_id}")

    def _get(self, path: str, err_msg: str | None = None) -> Any:
        self.__ensure_token()
        if self.session_token:
            return request("get", path, token=self.session_token, err_msg=err_msg)
        logger.info(f"NO ACCESSY SESSION TOKEN (ID or CLIENT not configured), skipping get from {path=}")
        return {}

    def __delete(self, path: str, err_msg: str | None = None, force_allow_modify: bool = False) -> Any:
        self.__ensure_token()
        if (ACCESSY_DO_MODIFY or force_allow_modify) and self.session_token:
            return request("delete", path, token=self.session_token, err_msg=err_msg)
        logger.info(f"ACCESSY_DO_MODIFY is false, skipping delete to {path=}")

    def __post(
        self,
        path: str,
        err_msg: str | None = None,
        json: dict[str, Any] | DataClassJsonMixin | None = None,
        force_allow_modify: bool = False,
    ) -> Any:
        self.__ensure_token()
        if (ACCESSY_DO_MODIFY or force_allow_modify) and self.session_token:
            return request("post", path, token=self.session_token, err_msg=err_msg, json=json)
        logger.info(f"ACCESSY_DO_MODIFY is false, skipping post to {path=}")

    def __put(
        self, path: str, err_msg: str | None = None, json: dict[str, Any] | DataClassJsonMixin | None = None
    ) -> Any:
        self.__ensure_token()
        if ACCESSY_DO_MODIFY and self.session_token:
            return request("put", path, token=self.session_token, err_msg=err_msg, json=json)
        logger.info(f"ACCESSY_DO_MODIFY is false, skipping put to {path=}")

    def _get_json_paginated(self, url: str, msg: str | None = None) -> list[Any]:
        """Convenience method for getting all data for a JSON endpoint that is paginated"""
        page_size = 10000
        page_number = 0
        items = []

        total_item_count = None
        received_item_count = 0
        while total_item_count is None or received_item_count < total_item_count:
            data = self._get(url + f"?page_number={page_number}&page_size={page_size}")
            current_items = data["items"]

            items.extend(current_items)
            received_item_count += len(current_items)
            page_number += 1
            if total_item_count and total_item_count != data["totalItems"]:
                logger.warning(f"Length of response was changed during fetch. Need to restart it.")
                return self._get_json_paginated(url, msg)
            total_item_count = data["totalItems"]

            if len(current_items) == 0 and total_item_count != 0:
                raise AccessyError(
                    f"Could not get all items. Not enough items were returned from Accessy endpoint during pagination loop. Got {received_item_count} out of {total_item_count} expected items"
                )

        return items

    def get_user_details(self, user_id: UUID) -> AccessyUser:
        """Get details for user ID."""
        json = self._get_user_details(user_id)
        try:
            return AccessyUser.from_dict(json)
        except Exception as e:
            raise AccessyError(
                f"Could not get user details for {user_id}. Could not deserialize {json} as an AccessyUser"
            ) from e

    ################################################
    # Methods that return raw JSON data from API:s
    ################################################

    def _get_user_details(self, user_id: UUID) -> Any:
        """Get details for user ID. Fields: id, msisdn, firstName, lastName, ..."""
        return self._get(f"/org/admin/user/{user_id}", err_msg="Getting user details")

    def _get_users_org(self) -> list[dict]:
        """Get all user ID:s"""
        return self._get_json_paginated(f"/asset/admin/organization/{self.organization_id()}/user")
        # {"items":[{"id":<uuid>,"msisdn":"+46...","firstName":str,"lastName":str}, ...],"totalItems":6,"pageSize":25,"pageNumber":0,"totalPages":1}

    def _get_users_in_access_group(self, access_group_id: UUID) -> list[dict]:
        """Get all user ID:s in a specific access group"""
        return self._get_json_paginated(f"/asset/admin/access-permission-group/{access_group_id}/membership")
        # {"items":[{"id":<uuid>,"userId":<uuid>,"organizationId":<uuid>,"roles":[<roles>]}, ...],"totalItems":3,"pageSize":25,"pageNumber":0,"totalPages":1}

    def _get_users_lab(self) -> list[dict]:
        """Get all user ID:s with lab access"""
        return self._get_users_in_access_group(ACCESSY_LABACCESS_GROUP)

    def _get_users_special(self) -> list[dict]:
        """Get all user ID:s with special access"""
        return self._get_users_in_access_group(ACCESSY_SPECIAL_LABACCESS_GROUP)

    def _get_organization_groups(self) -> list[dict]:
        """Get information about all groups"""
        return self._get_json_paginated(f"/asset/admin/organization/{self.organization_id()}/access-permission-group")
        # {"items": [{"id":<uuid>, "name":<string>, "description":<string>, constraints: <object>, childConstraints: <bool>}],"totalItems":2,"pageSize":25,"pageNumber":0,"totalPages":1}

    def _get_membership_ids_in_group(self, group_id: UUID) -> list[UUID]:
        """Get each membership for a specific group"""
        return [
            d["id"] for d in self._get_json_paginated(f"/asset/admin/access-permission-group/{group_id}/membership")
        ]

    def _get_group_description(self, group_id: UUID) -> str:
        """Get a description for a group ID"""
        name = self._get(f"/asset/admin/access-permission-group/{group_id}")["name"]
        assert isinstance(name, str)
        return name

    def _user_ids_to_accessy_members(self, user_ids: Iterable[UUID]) -> list[AccessyMember]:
        """Convert a list of User ID:s to AccessyMembers"""

        APPLICATION_PHONE_NUMBER = object()  # Sentinel phone number for applications

        def fill_user_details(user: AccessyMember) -> None:
            assert user.user_id is not None
            data = self.get_user_details(user.user_id)

            # API keys do not have phone numbers, set it to sentinel object so we can filter out API keys further down
            if data.application:
                user.phone = APPLICATION_PHONE_NUMBER
                return

            if data.msisdn is not None:
                user.phone = data.msisdn
            else:
                logger.warning(f"User {user.user_id} does not have a phone number in accessy. {data=}")
            user.name = f"{data.firstName} {data.lastName}"

        def fill_membership_id(user: AccessyMember) -> None:
            data = self._get(f"/asset/admin/user/{user.user_id}/organization/{self.organization_id()}/membership")
            user.membership_id = data["id"]

        threads = []
        accessy_members = []
        for uid in user_ids:
            accessy_member = AccessyMember(user_id=uid)
            threads.append(threading.Thread(target=fill_user_details, args=(accessy_member,)))
            threads.append(threading.Thread(target=fill_membership_id, args=(accessy_member,)))
            accessy_members.append(accessy_member)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Filter out API keys
        accessy_members = [m for m in accessy_members if m.phone is not APPLICATION_PHONE_NUMBER]

        return accessy_members

    def _get_org_user_from_phone(
        self, phone_number: MSISDN, users_in_org: list[dict] | None = None
    ) -> Union[None, AccessyMember]:
        """Get a AccessyMember from a phone number (if in org)"""
        if users_in_org is None:
            users_in_org = self._get_users_org()

        for item in users_in_org:
            if item.get("msisdn", None) == phone_number:
                user_id = item["id"]
                return self._user_ids_to_accessy_members([user_id])[0]
        else:
            return None

    def list_webhooks(self) -> list[AccessyWebhook]:
        hooks = self._get(f"/subscription/{self.organization_id()}/webhook")
        return [AccessyWebhook.from_dict(x) for x in hooks]

    def is_valid_webhook_signature(self, signature: str) -> bool:
        if self._all_webhooks is None:
            self._all_webhooks = self.list_webhooks()

        return signature in [webhook.signature for webhook in self._all_webhooks]

    def remove_webhook(self, id: UUID) -> Any:
        # Need to refetch webhooks
        self._all_webhooks = None
        return self.__delete(
            f"/subscription/{self.organization_id()}/webhook/{id}",
            force_allow_modify=True,
            err_msg="Failed to delete webhook",
        )

    def remove_all_webhooks(self) -> None:
        for webhook in self.list_webhooks():
            self.remove_webhook(webhook.id)

    def register_webhook(self, destinationURL: str, eventTypes: list[AccessyWebhookEventType]) -> None:
        # Need to refetch webhooks
        self._all_webhooks = self.list_webhooks()
        host = urlparse(destinationURL).hostname
        found_identical = False
        for w in self._all_webhooks:
            diff = w.destinationUrl != destinationURL or set([e.name for e in w.eventTypes]) != set(eventTypes)
            # Only remove webhooks for the same host
            # Other hosts can manage their own webhooks
            if urlparse(w.destinationUrl).hostname == host:
                if diff:
                    logger.info(f"Removing previous Accessy webhook for host {host} at {w.destinationUrl}")
                    self.remove_webhook(w.id)
                else:
                    found_identical = True

        if found_identical:
            logger.info(
                f"Accessy webhook already configured at {destinationURL}. There are currently {len(self._all_webhooks)} webhooks."
            )
            return None

        self.__post(
            f"/subscription/{self.organization_id()}/webhook",
            json=AccessyWebhookCreate(
                name="MakerAdmin",
                description="MakerAdmin webhook",
                destinationUrl=destinationURL,
                eventTypes=eventTypes,
            ),
            force_allow_modify=True,
        )

        self._all_webhooks = self.list_webhooks()
        logger.info(
            f"Registered Accessy webhook at {destinationURL}. There are currently {len(self._all_webhooks)} webhooks: {self._all_webhooks}"
        )


accessy_session = AccessySession() if AccessySession.is_env_configured() else None

STATUS_OK = 0
ERROR_NOT_CONFIGURED = 1


def register_accessy_webhook() -> bool:
    HOST_BACKEND: str = config.get("HOST_BACKEND").strip()
    webhook_url: str = f"{HOST_BACKEND}/accessy/event"
    if accessy_session is None:
        logger.warning(f"Accessy not configured. Skipping accessy webhook registration.")
        return False

    if webhook_url.startswith("https://"):
        webhook_create_lock = NamedAtomicLock("makeradmin_accessy_webhook_create_lock", maxLockAge=60 * 5)
        # We must ensure that only one instance of the server registers the webhook.
        # Otherwise we could end up with zero or many webhooks registered.
        if webhook_create_lock.acquire(timeout=15):
            try:
                accessy_session.register_webhook(
                    webhook_url,
                    [
                        AccessyWebhookEventType.ASSET_OPERATION_INVOKED,
                        AccessyWebhookEventType.ACCESS_REQUEST,
                        AccessyWebhookEventType.APPLICATION_ADDED,
                        AccessyWebhookEventType.APPLICATION_REMOVED,
                        AccessyWebhookEventType.GUEST_DOOR_ENTRY,
                        AccessyWebhookEventType.MEMBERSHIP_CREATED,
                        AccessyWebhookEventType.MEMBERSHIP_REMOVED,
                        AccessyWebhookEventType.MEMBERSHIP_REQUEST_CREATED,
                        AccessyWebhookEventType.MEMBERSHIP_REQUEST_APPROVED,
                        AccessyWebhookEventType.MEMBERSHIP_REQUEST_DENIED,
                        AccessyWebhookEventType.MEMBERSHIP_ROLE_ADDED,
                        AccessyWebhookEventType.MEMBERSHIP_ROLE_REMOVED,
                        AccessyWebhookEventType.ORGANIZATION_INVITATION_DELETED,
                    ],
                )
                return True
            finally:
                webhook_create_lock.release()
        else:
            logger.warning(f"Failed to acquire webhook create lock. Skipping accessy webhook registration.")
            return False
    else:
        logger.warning(f"Server is not running behind https. Skipping accessy webhook registration.")
        return False


def main() -> int:
    if accessy_session is None:
        print("Accessy not configured.")
        return ERROR_NOT_CONFIGURED
    pending_invitations = list(accessy_session.get_pending_invitations(date(2022, 8, 30)))
    print("Pending invitations", len(pending_invitations), pending_invitations)
    return STATUS_OK


if __name__ == "__main__":
    import sys

    sys.exit(main())
