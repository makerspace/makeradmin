from dataclasses import dataclass
from logging import getLogger
import os
import threading

import requests

from service.config import config

logger = getLogger("accessy")


UUID = str  # The UUID used by Accessy is a 16 byte hexadecimal number formatted as 01234567-abcd-abcd-abcd-0123456789ab (i.e. grouped by 4, 2, 2, 2, 6 with dashes in between)

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
        if not isinstance(client_id, str) or not isinstance(client_secret, str):
            raise TypeError("client_id and client_secret must be strings")

        response = requests.post(ACCESSY_URL + "/auth/oauth/token", 
            json={"audience": ACCESSY_URL, "grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            headers={"Content-Type": "application/json"}
        )
        if not response.ok:
            return None
        return cls(response.json()["access_token"])
    
    def __post_init__(self):
        self.organization_id = self.__get_organization()

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
        check_response_error(response, f"{msg}")
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
            response = requests.get(ACCESSY_URL + url + f"?page_number={page_number}&page_size={page_size}",
                                    headers={"Authorization": f"Bearer {self.session_token}"})
            check_response_error(response, f"{msg} (when fetching items {received_item_count} / {total_item_count})")
            data = response.json()

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

        def fill_user_details(user: "AccessyMember", user_id: str):
            data = self._get_json(f"/org/admin/user/{user_id}")

            # API keys do not have phone numbers
            if data["application"]:
                return

            try:
                user.phone_number = data["msisdn"]
            except KeyError:
                logger.error(f"User {user.user_id} does not have a phone number. {data=}")

        def fill_membership_id(user: "AccessyMember", user_id: str):
            data = self._get_json(f"/asset/admin/user/{user_id}/organization/{self.organization_id}/membership")
            user.membership_id = data["id"]
        
        threads = []
        accessy_members = []
        for uid in user_ids:
            accessy_member = AccessyMember(uid, None)
            threads.append(threading.Thread(target=fill_user_details, args=(accessy_member, uid)))
            threads.append(threading.Thread(target=fill_membership_id, args=(accessy_member, uid)))
            accessy_members.append(accessy_member)
        
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        return accessy_members
    
    #################
    # Public methods
    #################

    def get_all_members(self) -> tuple[list["AccessyMember"], list["AccessyMember"], list["AccessyMember"]]:
        """ Get a list of all Accessy members in the ORG and GROUPS (lab and special) """
        org = set(item["id"] for item in self._get_users_org())
        lab = set(item["userId"] for item in self._get_users_lab())
        special = set(item["userId"] for item in self._get_users_special())

        org = self._user_ids_to_accessy_members(org)
        lab = self._user_ids_to_accessy_members(lab)
        special = self._user_ids_to_accessy_members(special)

        return org, lab, special


@dataclass
class AccessyMember:
    user_id: UUID
    phone_number: str
    membership_id: UUID = None


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
    org, lab, special = session.get_all_members()
    print("Members in organization: ", org)
    print("Members in lab group: ", lab)
    print("Members in special group: ", special)


if __name__ == "__main__":
    main()
