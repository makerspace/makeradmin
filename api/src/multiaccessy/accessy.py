import threading
from collections.abc import Iterable

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from logging import getLogger
from random import random, randint
from time import sleep
from typing import Union

import dateutil.parser
import requests

from service.config import config
from service.entity import fromisoformat

logger = getLogger("accessy")


class AccessyError(RuntimeError):
    pass


PHONE = str
UUID = str  # The UUID used by Accessy is a 16 byte hexadecimal number formatted as 01234567-abcd-abcd-abcd-0123456789ab (i.e. grouped by 4, 2, 2, 2, 6 with dashes in between)
MSISDN = str  # Standardized number of the form +46123123456

ACCESSY_URL = config.get("ACCESSY_URL")
ACCESSY_CLIENT_SECRET = config.get("ACCESSY_CLIENT_SECRET", log_value=False)
ACCESSY_CLIENT_ID = config.get("ACCESSY_CLIENT_ID")
ACCESSY_LABACCESS_GROUP = config.get("ACCESSY_LABACCESS_GROUP")
ACCESSY_SPECIAL_LABACCESS_GROUP = config.get("ACCESSY_SPECIAL_LABACCESS_GROUP")
ACCESSY_DO_MODIFY = config.get("ACCESSY_DO_MODIFY", default="false").lower() == "true"


def request(method, path, token=None, json=None, max_tries=8, err_msg=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json:
        headers["Content-Type"] = "application/json"
        
    backoff = 1.0
    for i in range(max_tries):
        response = requests.request(method, ACCESSY_URL + path, json=json, headers=headers)
        if response.status_code == 429:
            logger.warning(f"requesting accessy returned 429, too many reqeusts, try {i+1}/{max_tries}, retrying in {backoff}s, {path=}")
            sleep(backoff)
            backoff = backoff * (1.2 + 0.1 * random())
            continue

        if response.status_code == 401:
            raise AccessyError("401: unauthorized")

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


@dataclass
class AccessyDoor:
    id: UUID = field(repr=False)
    name: str

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Access:
    dt: datetime
    name: str
    door: AccessyDoor = field(repr=False)

    def __hash__(self) -> int:
        return hash((self.dt, self.name, self.door))


@dataclass
class AccessyMember:
    user_id: Union[UUID, None] = None
    # Get information below later
    phone: Union[str, None] = None
    membership_id: Union[UUID, None] = field(default=None)
    name: str = "<name>"
    member_id: Union[int, None] = None  # Makeradmin member_id
    member_number: Union[int, None] = None  # Makeradmin member_number
    groups: {str} = field(default_factory=set)

    def __repr__(self):
        groups = []
        if ACCESSY_LABACCESS_GROUP in self.groups:
            groups.append("labaccess")
        if ACCESSY_SPECIAL_LABACCESS_GROUP in self.groups:
            groups.append("special")
        return f"AccessyMember(phone={self.phone}, name={self.name}, {groups=}, member_id={self.member_id}, member_number={self.member_number}, user_id={self.user_id})"


class AccessySession:
    def __init__(self):
        self.session_token = None
        self.session_token_token_expires_at = None
        self._organization_id = None
        self._mutex = threading.Lock()

    #################
    # Public methods
    #################

    def get_all_members(self) -> list[AccessyMember]:
        """ Get a list of all Accessy members in the ORG with GROUPS (lab and special) """

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

    def is_in_org(self, phone_number: MSISDN, users_org: list[dict] = None) -> bool:
        """ Check if a user with a specific phone number is in the ORG """
        user = self._get_org_user_from_phone(phone_number, users_org)
        if user is not None:
            return True
        return False

    def is_in_group(self, phone_number: MSISDN, access_group_id: UUID) -> bool:
        """ Check if a user is in a specific access group """
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return False

        membership_ids = self._get_membership_ids_in_group(access_group_id)
        for id_ in membership_ids:
            if id_ == accessy_member.membership_id:
                return True
        return False

    def remove_from_org(self, phone_number: MSISDN):
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return

        self.__delete(f"/org/admin/organization/{self.organization_id()}/user/{accessy_member.user_id}")

    def remove_from_group(self, phone_number: MSISDN, access_group_id: UUID):
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return

        self.__delete(f"/asset/admin/access-permission-group/{access_group_id}/membership/{accessy_member.membership_id}")

    def add_to_group(self, phone_number: MSISDN, access_group_id: UUID):
        """ Add a specific user with phone number to access group """
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            self.invite_phone_to_org_and_groups([phone_number], [access_group_id])

        self.__put(
            f"/asset/admin/access-permission-group/{access_group_id}/membership",
            json=dict(membership=accessy_member.membership_id),
        )

    def invite_phone_to_org_and_groups(self, phone_numbers: Iterable[MSISDN], access_group_ids: Iterable[UUID] = [], message_to_user: str = ""):
        """ Invite a list of phone numbers to a list of groups """
        self.__post(
            f"/org/admin/organization/{self.organization_id()}/invitation",
            json=dict(accessPermissionGroupIds=list(access_group_ids), message=message_to_user, msisdns=list(phone_numbers)),
            err_msg=f"invite {phone_numbers=} to org and groups {access_group_ids}. {message_to_user=}",
        )
    
    def get_pending_invitations(self, after_date: date = None) -> Iterable[MSISDN]:
        """ Get all pending invitations after a specific date (including). """
        data = self._get(f"/org/admin/organization/{self.organization_id()}/invitation")
        pending_invitations = set()
        for inv in data:
            recipient = inv["recipientMsisdn"]
            invitation_date = fromisoformat(inv["createdAt"]).date()
            is_pending = inv["status"] == "PENDING"

            if is_pending and (after_date is None or invitation_date >= after_date):
                pending_invitations.add(recipient)
        return pending_invitations
        
    def organization_id(self):
        if self._organization_id:
            return self._organization_id
        self.__ensure_token()
        return self._organization_id
    
    def get_user_groups(self, phone_number: MSISDN) -> list[str]:
        """ Get all of the groups of a member """
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return []

        org_groups = (d['id'] for d in self._get_organization_groups())

        group_descriptions = []
        for group_id in org_groups:
            membership_ids = self._get_membership_ids_in_group(group_id)
            if accessy_member.membership_id in membership_ids:
                group_descriptions.append(self._get_group_description(group_id))

        return group_descriptions
    
    def get_all_doors(self) -> list[AccessyDoor]:
        items = self._get_doors()
        doors = [AccessyDoor(item["id"], item["name"]) for item in items]
        for door in doors:
            door.id = self._get_asset_id(door.id)
        return doors

    def get_all_accesses(self, door: AccessyDoor) -> list[Access]:
        response = self._get_accesses(door.id)
        accesses = []
        for item in response["items"]:
            dt = dateutil.parser.parse(item["date"])
            name = item["user"]
            accesses.append(Access(dt, name, door))
        return accesses

    ################################################
    # Internal methods
    ################################################

    def refresh_token(self):
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
        logger.info(f"accessy session token refreshed, expires_at={self.session_token_token_expires_at.isoformat()} token={self.session_token}")

    def fetch_organization_id(self) -> UUID:
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

        return data[0]["organizationId"]

    def __ensure_token(self):
        if not ACCESSY_CLIENT_ID or not ACCESSY_CLIENT_SECRET:
            return

        with self._mutex:  # Only allow one concurrent token refresh as rate limiting on this endpoint is aggressive.
            if not self.session_token or datetime.now() > self.session_token_token_expires_at - timedelta(hours=randint(1, 23), minutes=randint(0, 59)):
                self.refresh_token()

            try:
                organization_id = self.fetch_organization_id()
            except AccessyError as e:
                if "401" not in str(e):
                    raise e

                self.refresh_token()
                organization_id = self.fetch_organization_id()
            finally:
                if not self._organization_id:
                    self._organization_id = organization_id
                    logger.info(f"fetched accessy organization_id {self._organization_id}")

    def _get(self, path: str, err_msg: str = None) -> dict:
        self.__ensure_token()
        if self.session_token:
            return request("get", path, token=self.session_token, err_msg=err_msg)
        logger.info(f"NO ACCESSY SESSION TOKEN (ID or CLIENT not configured), skipping get from {path=}")
        return {}

    def __delete(self, path: str, err_msg: str = None):
        self.__ensure_token()
        if ACCESSY_DO_MODIFY and self.session_token:
            return request("delete", path, token=self.session_token, err_msg=err_msg)
        logger.info(f"ACCESSY_DO_MODIFY is false, skipping delete to {path=}")
    
    def __post(self, path: str, err_msg: str = None, json: dict = None):
        self.__ensure_token()
        if ACCESSY_DO_MODIFY and self.session_token:
            return request("post", path, token=self.session_token, err_msg=err_msg, json=json)
        logger.info(f"ACCESSY_DO_MODIFY is false, skipping post to {path=}")

    def __put(self, path: str, err_msg: str = None, json: dict = None):
        self.__ensure_token()
        if ACCESSY_DO_MODIFY and self.session_token:
            return request("put", path, token=self.session_token, err_msg=err_msg, json=json)
        logger.info(f"ACCESSY_DO_MODIFY is false, skipping put to {path=}")

    def _get_json_paginated(self, url: str, msg: str = None):
        """ Convenience method for getting all data for a JSON endpoint that is paginated """
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
                raise AccessyError(f"Could not get all items. Not enough items were returned from Accessy endpoint during pagination loop. Got {received_item_count} out of {total_item_count} expected items")

        return items

    ################################################
    # Methods that return raw JSON data from API:s
    ################################################

    def _get_user_details(self, user_id: UUID) -> dict:
        """ Get details for user ID. Fields: id, msisdn, firstName, lastName, ... """
        return self._get(f"/org/admin/user/{user_id}", err_msg="Getting user details")

    def _get_users_org(self) -> list[dict]:
        """ Get all user ID:s """
        return self._get_json_paginated(f"/asset/admin/organization/{self.organization_id()}/user")
        # {"items":[{"id":<uuid>,"msisdn":"+46...","firstName":str,"lastName":str}, ...],"totalItems":6,"pageSize":25,"pageNumber":0,"totalPages":1}
    
    def _get_users_in_access_group(self, access_group_id: UUID) -> list[dict]:
        """ Get all user ID:s in a specific access group """
        return self._get_json_paginated(f"/asset/admin/access-permission-group/{access_group_id}/membership")
        # {"items":[{"id":<uuid>,"userId":<uuid>,"organizationId":<uuid>,"roles":[<roles>]}, ...],"totalItems":3,"pageSize":25,"pageNumber":0,"totalPages":1}

    def _get_users_lab(self) -> list[dict]:
        """ Get all user ID:s with lab access """
        return self._get_users_in_access_group(ACCESSY_LABACCESS_GROUP)

    def _get_users_special(self) -> list[dict]:
        """ Get all user ID:s with special access """
        return self._get_users_in_access_group(ACCESSY_SPECIAL_LABACCESS_GROUP)
    
    def _get_organization_groups(self) -> list[dict]:
        """ Get information about all groups """
        return self._get_json_paginated(f"/asset/admin/organization/{self.organization_id()}/access-permission-group")
        # {"items": [{"id":<uuid>, "name":<string>, "description":<string>, constraints: <object>, childConstraints: <bool>}],"totalItems":2,"pageSize":25,"pageNumber":0,"totalPages":1}
    
    def _get_membership_ids_in_group(self, group_id: UUID) -> list[UUID]:
        """ Get each membership for a specific group """
        return [d["id"] for d in self._get_json_paginated(f"/asset/admin/access-permission-group/{group_id}/membership")]
    
    def _get_group_description(self, group_id: UUID) -> str:
        """ Get a description for a group ID """
        return self._get(f"/asset/admin/access-permission-group/{group_id}")["name"]

    def _user_ids_to_accessy_members(self, user_ids: Iterable[UUID]) -> list[AccessyMember]:
        """ Convert a list of User ID:s to AccessyMembers """

        APPLICATION_PHONE_NUMBER = object()  # Sentinel phone number for applications
        def fill_user_details(user: AccessyMember):
            data = self._get(f"/org/admin/user/{user.user_id}")

            # API keys do not have phone numbers, set it to sentinel object so we can filter out API keys further down
            if data["application"]:
                user.phone = APPLICATION_PHONE_NUMBER
                return

            try:
                user.phone = data["msisdn"]
            except KeyError:
                logger.warning(f"User {user.user_id} does not have a phone number in accessy. {data=}")
            user.name = f"{data.get('firstName', '')} {data.get('lastName', '')}"

        def fill_membership_id(user: AccessyMember):
            data = self._get(f"/asset/admin/user/{user.user_id}/organization/{self.organization_id()}/membership")
            user.membership_id = data["id"]
        
        threads = []
        accessy_members = []
        for uid in user_ids:
            accessy_member = AccessyMember(user_id=uid)
            threads.append(threading.Thread(target=fill_user_details, args=(accessy_member, )))
            threads.append(threading.Thread(target=fill_membership_id, args=(accessy_member, )))
            accessy_members.append(accessy_member)
        
        for t in threads:
            t.start()

        for t in threads:
            t.join()
        
        # Filter out API keys
        accessy_members = [m for m in accessy_members if m.phone is not APPLICATION_PHONE_NUMBER]

        return accessy_members
    
    def _get_org_user_from_phone(self, phone_number: MSISDN, users_in_org: list[dict] = None) -> Union[None, AccessyMember]:
        """ Get a AccessyMember from a phone number (if in org) """
        if users_in_org is None:
            users_in_org = self._get_users_org()

        for item in users_in_org:
            if item.get("msisdn", None) == phone_number:
                user_id = item["id"]
                return self._user_ids_to_accessy_members([user_id])[0]
        else:
            return None
    
    def _get_asset_id(self, door_id: UUID) -> UUID:
        return self._get(f"/asset/admin/organization/{self.organization_id()}/asset/{door_id}/asset-publication")["id"]

    def _get_doors(self):
        return self._get_json_paginated(f"/asset/admin/organization/{self.organization_id()}/asset")
    
    def _get_accesses(self, door_id: UUID):
        return self._get(f"/asset/admin/asset-publication/{door_id}/invoke-activity?cursor=&page_size=250&")


accessy_session = AccessySession()


def main():
    pending_invitations = accessy_session.get_pending_invitations(date(2022, 8, 30))
    print("Pending invitations", len(pending_invitations), pending_invitations)


if __name__ == "__main__":
    main()
