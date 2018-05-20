from collections import namedtuple

import requests

MakerAdminMember = namedtuple('MemberInfo', [
    'member_id',      # int for debugging
    'member_number',  # int
    'firstname',      # string
    'lastname',       # string
    'key_id',         # int for debugging
    'rfid_tag',       # string
    'blocked',        # bool
    'end_timestamp',  # string timestamp in zulu
])

class APIGateway:
    def __init__(self, host, key=""):
        self.host = host
        self.key = key

    def login(self, username, password):
        r = self.post("oauth/token", { "grant_type": "password", "username": username, "password": password })
        if not r.ok:
            raise Exception("Failed to login\n" + r.text)
        self.key = r.json()["access_token"]

    def _transport(self, url):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        return url

    def _headers(self):
        return {"Authorization": "Bearer " + self.key}

    def get(self, path, payload=None):
        return requests.get(self._transport(self.host + "/" + path), params=payload, headers=self._headers())

    def post(self, path, payload):
        return requests.post(self._transport(self.host + "/" + path), json=payload, headers=self._headers())

    def put(self, path, payload):
        return requests.put(self._transport(self.host + "/" + path), json=payload, headers=self._headers())


class MakerAdminClient(object):
    
    def __init__(self, base_url):
        self.gateway = APIGateway(base_url)

    # TODO Write tests for when this it is known it should work.
    def fetch_members(self, ui):
        """ Fetch and return list of MakerAdminMember, raises exception on error. """
        ui.info__progress(f"Downloading member list...")
        r = self.gateway.get("auto/multiaccess/members")

        res = [MakerAdminMember(**m) for m in r.json()]

        ui.info__progress(f"got {len(res)} members")

        return res
