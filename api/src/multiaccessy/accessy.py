from dataclasses import dataclass, field
from logging import getLogger
import os
import threading
from typing import Union

import requests

from service.config import config

logger = getLogger("accessy")


UUID = str  # The UUID used by Accessy is a 16 byte hexadecimal number formatted as 01234567-abcd-abcd-abcd-0123456789ab (i.e. grouped by 4, 2, 2, 2, 6 with dashes in between)
MSISDN = str  # Standardized number of the form +46123123456

ACCESSY_URL = config.get("ACCESSY_URL")
ACCESSY_CLIENT_SECRET = config.get("ACCESSY_CLIENT_SECRET", log_value=False)
ACCESSY_CLIENT_ID = config.get("ACCESSY_CLIENT_ID")
ACCESSY_LAB_ACCESS_GROUP = config.get("ACCESSY_LAB_ACCESS_GROUP")
ACCESSY_SPECIAL_ACCESS_GROUP = config.get("ACCESSY_SPECIAL_ACCESS_GROUP")


def check_response_error(response: requests.Response, msg: str = None):
    if not response.ok:
        msg_str = f"\n\tMessage: {msg}" if msg is not None else ""
        logger.error(f"Got an error in the response for {response.request.path_url}. {response.status_code=}{msg_str}")
        raise RuntimeError(msg)


@dataclass
class AccessySession:
    session_token: UUID

    @classmethod
    def create_session(cls, client_id: str, client_secret: str) -> "AccessySession":
        response = requests.post(ACCESSY_URL + "/auth/oauth/token", 
            json={"audience": ACCESSY_URL, "grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            headers={"Content-Type": "application/json"}
        )
        if not response.ok:
            return None
        return cls(response.json()["access_token"])
    
    def __post_init__(self):
        self.organization_id = self.__get_organization()

    #################
    # Public methods
    #################
    @dataclass
    class AllAccessyMemberGroups:
        """ A collection of the members that are included in each Accessy org/group """
        org_members: list["AccessyMember"]
        lab: list["AccessyMember"]
        special: list["AccessyMember"]

    def get_all_groups_members(self) -> AllAccessyMemberGroups:
        """ Get a list of all Accessy members in the ORG and GROUPS (lab and special) """
        org = set(item["id"] for item in self._get_users_org())
        lab = set(item["userId"] for item in self._get_users_lab())
        special = set(item["userId"] for item in self._get_users_special())

        return AccessySession.AllAccessyMemberGroups(
            org_members=self._user_ids_to_accessy_members(org),
            lab=self._user_ids_to_accessy_members(lab),
            special=self._user_ids_to_accessy_members(special)
        )

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

        items = self._get_json_paginated(f"/asset/admin/access-permission-group/{access_group_id}/membership")
        for item in items:
            if item["userId"] == accessy_member.user_id:
                return True
        return False

    def remove_from_org(self, phone_number: MSISDN):
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return

        response = requests.delete(ACCESSY_URL + f"/org/admin/organization/{self.organization_id}/user/{accessy_member.user_id}",
                                   headers={"Authorization": f"Bearer {self.session_token}"})
        check_response_error(response)

    def remove_from_group(self, phone_number: MSISDN, access_group_id: UUID):
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            return

        response = requests.delete(ACCESSY_URL + f"/asset/admin/access-permission-group/{access_group_id}/membership/{accessy_member.membership_id}",
                                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.session_token}"})
        check_response_error(response)

    def add_to_group(self, phone_number: MSISDN, access_group_id: UUID):
        """ Add a specific user with phone number to access group """
        accessy_member = self._get_org_user_from_phone(phone_number)
        if accessy_member is None:
            self.invite_phone_to_org_and_groups([phone_number], [access_group_id])

        response = requests.put(ACCESSY_URL + f"/asset/admin/access-permission-group/{access_group_id}/membership", json=dict(membership=accessy_member.membership_id),
                                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.session_token}"})
        check_response_error(response)

    def invite_phone_to_org_and_groups(self, phone_numbers: list[MSISDN], access_group_ids: list[UUID] = [], message_to_user: str = ""):
        """ Invite a list of phone numbers to a list of groups """
        response = requests.post(ACCESSY_URL + f"/org/admin/organization/{self.organization_id}/invitation",
                                json=dict(accessPermissionGroupIds=access_group_ids, message=message_to_user, msisdns=phone_numbers),
                                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.session_token}"})
        check_response_error(response, f"Invite {phone_numbers=} to org and groups {access_group_ids}. {message_to_user=}")

    ################################################
    # Internal methods
    ################################################

    def __get_organization(self) -> str:
        """ Get the organization for the session token """
        data = self._get_json("/asset/user/organization-membership")
        # [{"id":<uuid>,"userId":<uuid>,"organizationId":<uuid>,"roles":[<roles>]}]
        if len(data) > 1:
            logger.warning("API key has several memberships. This is probably an error...")
        elif len(data) == 0:
            raise ValueError("The API key does not have a corresponding organization membership")

        return data[0]["organizationId"]

    def _get_json(self, url: str, msg: str = None) -> dict:
        """ Convenience method for getting data from a JSON endpoint that is not paginated """
        response = requests.get(ACCESSY_URL + url,
                                headers={"Authorization": f"Bearer {self.session_token}"})
        check_response_error(response, msg)
        data = response.json()
        return data
    
    def _get_json_paginated(self, url: str, msg: str = None):
        """ Convenience method for getting all data for a JSON endpoint that is paginated """
        page_size = 10000
        page_number = 0
        items = []

        total_item_count = None
        received_item_count = 0
        while total_item_count is None or received_item_count < total_item_count:
            data = self._get_json(url + f"?page_number={page_number}&page_size={page_size}")
            current_items = data["items"]

            items.extend(current_items)
            received_item_count += len(current_items)
            page_number += 1
            if total_item_count and total_item_count != data["totalItems"]:
                logger.warning(f"Length of response was changed during fetch. Need to restart it.")
                return self._get_json_paginated(url, msg)
            total_item_count = data["totalItems"]

            if len(current_items) == 0 and total_item_count != 0:
                raise ValueError(f"Could not get all items. Not enough items were returned from Accessy endpoint during pagination loop. Got {received_item_count} out of {total_item_count} expected items")

        return items
    
    ################################################
    # Methods that return raw JSON data from API:s
    ################################################

    def _get_user_details(self, user_id: UUID) -> dict:
        """ Get details for user ID. Fields: id, msisdn, firstName, lastName, ... """
        return self._get_json(f"/org/admin/user/{user_id}", msg="Getting user details")

    def _get_users_org(self) -> list[dict]:
        """ Get all user ID:s """
        return self._get_json_paginated(f"/asset/admin/organization/{self.organization_id}/user")
        # {"items":[{"id":<uuid>,"msisdn":"+46...","firstName":str,"lastName":str}, ...],"totalItems":6,"pageSize":25,"pageNumber":0,"totalPages":1}
    
    def _get_users_in_access_group(self, access_group_id: UUID) -> list[dict]:
        """ Get all user ID:s in a specific access group """
        return self._get_json_paginated(f"/asset/admin/access-permission-group/{access_group_id}/membership")
        # {"items":[{"id":<uuid>,"userId":<uuid>,"organizationId":<uuid>,"roles":[<roles>]}, ...],"totalItems":3,"pageSize":25,"pageNumber":0,"totalPages":1}

    def _get_users_lab(self) -> list[dict]:
        """ Get all user ID:s with lab access """
        return self._get_users_in_access_group(ACCESSY_LAB_ACCESS_GROUP)

    def _get_users_special(self) -> list[dict]:
        """ Get all user ID:s with special access """
        return self._get_users_in_access_group(ACCESSY_SPECIAL_ACCESS_GROUP)
    
    def _user_ids_to_accessy_members(self, user_ids: list[UUID]) -> list["AccessyMember"]:
        """ Convert a list of User ID:s to AccessyMembers """

        APPLICATION_PHONE_NUMBER = object()  # Sentinel phone number for applications
        def fill_user_details(user: "AccessyMember"):
            data = self._get_json(f"/org/admin/user/{user.user_id}")

            # API keys do not have phone numbers, set it to sentinel object so we can filter out API keys further down
            if data["application"]:
                user.phone_number = APPLICATION_PHONE_NUMBER
                return

            try:
                user.phone_number = data["msisdn"]
            except KeyError:
                logger.error(f"User {user.user_id} does not have a phone number. {data=}")
            user.first_name = data.get("firstName", "")
            user.last_name = data.get("lastName", "")

        def fill_membership_id(user: "AccessyMember"):
            data = self._get_json(f"/asset/admin/user/{user.user_id}/organization/{self.organization_id}/membership")
            user.membership_id = data["id"]
        
        threads = []
        accessy_members = []
        for uid in user_ids:
            accessy_member = AccessyMember(uid)
            threads.append(threading.Thread(target=fill_user_details, args=(accessy_member, )))
            threads.append(threading.Thread(target=fill_membership_id, args=(accessy_member, )))
            accessy_members.append(accessy_member)
        
        for t in threads:
            t.start()

        for t in threads:
            t.join()
        
        # Filter out API keys
        accessy_members = [m for m in accessy_members if m.phone_number is not APPLICATION_PHONE_NUMBER]

        return accessy_members
    
    def _get_org_user_from_phone(self, phone_number: MSISDN, users_in_org: list[dict] = None) -> Union[None, "AccessyMember"]:
        """ Get a AccessyMember from a phone number (if in org) """
        if users_in_org is None:
            users_in_org = self._get_users_org()

        for item in users_in_org:
            if item.get("msisdn", None) == phone_number:
                user_id = item["id"]
                return self._user_ids_to_accessy_members([user_id])[0]
        else:
            return None


@dataclass
class AccessyMember:
    user_id: UUID = field(repr=False)
    # Get information below later
    phone_number: str = None
    membership_id: UUID = field(repr=False, default=None)
    first_name: str = "<first name>"
    last_name: str = "<last name>"


def main():
    session = None
    # Convenience if a session token is already issued
    session_token = os.environ.get("ACCESSY_SESSION_TOKEN")
    try:
        session = AccessySession(session_token)
    except:
        pass

    # Get a new session token
    if session is None:
        session = AccessySession.create_session(ACCESSY_CLIENT_ID, ACCESSY_CLIENT_SECRET)
    print("session:", session)
    all_groups = session.get_all_groups_members()
    print("Members in organization: ", all_groups.org_members)
    print("Members in lab group: ", all_groups.lab)
    print("Members in special group: ", all_groups.special)

    # Check person is in ORG
    import random
    random_se_number = f"+46{random.randint(0, 1e9):09d}"
    print(f"Random person ({random_se_number}) in org?: {session.is_in_org(random_se_number)}")
    special_person = random.choice(all_groups.special)
    print(f"Special person ({special_person.phone_number}) in org?: {session.is_in_org(special_person.phone_number)}")


if __name__ == "__main__":
    main()
