from dataclasses import dataclass, field
from logging import getLogger
import os
import threading
import uuid
import warnings

import requests

from service.config import config

logger = getLogger("accessy")


ACCESSY_URL = config.get("ACCESSY_URL")
ACCESSY_CLIENT_SECRET = config.get("ACCESSY_CLIENT_SECRET", log_value=False)
ACCESSY_CLIENT_ID = config.get("ACCESSY_CLIENT_ID")


def check_response_error(response: requests.Response, msg: str = None):
    if not response.ok:
        msg_str = f"\n\tMessage: {msg}" if msg is not None else ""
        logger.error(f"Got an error in the response. {response.status_code=}{msg_str}")
        raise RuntimeError(msg)


@dataclass
class AccessySession:
    session_token: uuid

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
        self.organization_id = self._get_organization()
    
    def _get_json_paginated(self, url: str, msg: str = None):
        """ Convenience method for getting all data for a JSON endpoint that is paginated """
        page_size = 10000
        page_number = 0
        items = []

        total_items = None
        received_items = 0
        while total_items is None or received_items < total_items:
            response = requests.get(ACCESSY_URL + url + f"?page_number={page_number}&page_size={page_size}",
                                    headers={"Authorization": f"Bearer {self.session_token}"})
            check_response_error(response, f"{msg} (on page {page_number})")
            data = response.json()

            current_items = data["items"]

            items.extend(current_items)
            received_items += len(current_items)
            page_number += 1
            if total_items and total_items != data["totalItems"]:
                logger.warning(f"Length of response was changed during fetch. Need to restart it.")
                return self._get_json_paginated(url, msg)
            total_items = data["totalItems"]

            if len(current_items) == 0:
                raise ValueError(f"Could not get all items. Not enough items were returned from Accessy endpoint during pagination loop. Got {len(received_items)} out of {total_items} expected items")

        return items

    def _get_organization(self) -> str:
        """ Get the organization for the session token """
        response = requests.get(ACCESSY_URL + "/asset/user/organization-membership",
                                headers={"Authorization": f"Bearer {self.session_token}"})
        # [{"id":<uuid>,"userId":<uuid>,"organizationId":<uuid>,"roles":[<roles>]}]

        check_response_error(response, "Get organization")

        data = response.json()
        if len(data) > 1:
            warnings.warn("API key has several memberships. This is probably an error...", RuntimeWarning)
        elif len(data) == 0:
            raise ValueError("The API key does not have a corresponding organization membership")

        return data[0]["organizationId"]

    def get_users_org(self) -> list[dict]:
        """ Get all user ID:s """
        return self._get_json_paginated(f"/asset/admin/organization/{self.organization_id}/user")
        # {"items":[{"id":<uuid>,"msisdn":"+46...","firstName":str,"lastName":str}, ...],"totalItems":6,"pageSize":25,"pageNumber":0,"totalPages":1}
    
    def get_users_lab(self) -> list[dict]:
        """ Get all user ID:s with lab access """
        pass
    
    def get_users_special(self) -> list[dict]:
        """ Get all user ID:s with special access """
        pass

    def get_membership(self, user_id: str) -> str:
        """ Get the membership ID for a user ID """
        response = requests.get(ACCESSY_URL + f"/asset/admin/user/{user_id}/organization/{self.organization_id}/membership",
                                headers={"Authorization": f"Bearer {self.session_token}"})

        check_response_error(response, "Get membership")
        data = response.json()
        return data["id"]

    def get_all_members(self) -> tuple[list["AccessyMember"], list["AccessyMember"], list["AccessyMember"]]:
        """ Get a list of all Accessy members in ORG, GROUP (lab and special) """
        org = self.get_users_org()
        lab = self.get_users_lab()
        special = self.get_users_special()

        def get_membership(user: "AccessyMember", user_id: str):
            user.membership_id = self.get_membership(user_id)

        accessy_users = []
        # Fill in the membership ID for all
        threads = []
        for user in org:
            # API key does not have phone number
            phone_number = user.get("msisdn", None)
            if phone_number is None:
                continue

            user_id = user["id"]

            # Create user without membership, then update in-place in parallel
            accessy_user = AccessyMember(user_id, phone_number)
            accessy_users.append(accessy_user)
            _thread = threading.Thread(target=get_membership, args=(accessy_user, user_id), daemon=True)
            _thread.start()
            threads.append(_thread)

        for thread in threads:
            thread.join()

        return org, lab, special


@dataclass
class AccessyMember:
    user_id: uuid
    phone_number: str
    membership_id: uuid = None


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
    users = session.get_all_members()
    print("users:", users)


if __name__ == "__main__":
    main()
