import json
from collections import namedtuple
from os.path import join
from tempfile import gettempdir

import requests
from iso8601 import ParseError

from multi_access.util import dt_parse, to_cet
from jsonschema import validate, ValidationError

schema = dict(
    type="array",
    items=dict(
        type="object",
        properties=dict(
            member_id=dict(type="integer"),
            member_number=dict(type="integer"),
            firstname=dict(type="string"),
            lastname=dict(type="string"),
            keys=dict(
                type="array",
                items=dict(
                    type="object",
                    properties=dict(
                        key_id=dict(type="integer"),
                        rfid_tag=dict(type="string", pattern=r"^\w+$", maxLength=12),
                        blocked=dict(type="boolean"),
                        end_timestamp=dict(type=["string", "null"]),
                        start_timestamp=dict(type=["string", "null"]),
                    ),
                )
            )
        )
    )
)


MakerAdminMember = namedtuple('MakerAdminMember', [
    'member_number',  # int
    'firstname',      # string
    'lastname',       # string
    'rfid_tag',       # string
    'end_timestamp',  # string timestamp in zulu
])


class MakerAdminClient(object):
    
    def __init__(self, ui=None, base_url=None, members_filename=None, tokenfilename=None):
        self.ui = ui
        self.base_url = base_url
        self.members_filename = members_filename
        self.tokenfile = tokenfilename or join(gettempdir(), 'LFP7EL5K6SFF.TXT')
        try:
            with open(self.tokenfile) as r:
                self.token = r.read().strip()
        except OSError:
            self.token = 'nokey'
        
    def login(self):
        username, password = self.ui.promt__login()
        r = requests.post(self.base_url + "/oauth/token",
                          {"grant_type": "password", "username": username, "password": password})
        
        if not r.ok:
            return
        self.token = r.json()["access_token"]
        with open(self.tokenfile, 'w') as w:
            w.write(self.token)
    
    def get_and_login_if_needed(self, url):
        for i in range(3):
            r = requests.get(url, headers={'Authorization': 'Bearer ' + self.token})
            if r.ok:
                return r.json()
            elif r.status_code == 401:
                print(r.content, r.status_code)
                self.login()
            else:
                self.ui.fatal__error(f"failed to get data, got ({r.status_code}):\n" + r.text)
        else:
            self.ui.fatal__error("failed to login")

    def fetch_members(self, ui):
        """ Fetch and return list of MakerAdminMember, raises exception on error. """
        if self.members_filename:
            ui.info__progress(f"getting members from file {self.members_filename}")
            with open(self.members_filename) as f:
                data = json.load(f)
        else:
            url = self.base_url + '/multiaccess/memberdata'
            ui.info__progress(f"getting members from {url}")
            data = self.get_and_login_if_needed(url)['data']
            from pprint import pprint
            pprint(data)
            
        res = self.response_data_to_members(data)
        
        ui.info__progress(f"got {len(res)} members")

        return res

    @staticmethod
    def response_data_to_members(data):
        """ Convert data object form server or file to filtered MakerAdminMember list (also parse timestamp). """
        
        try:
            validate(data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Failed to parse member data: {str(e)}") from e

        def create_maker_admin(item):
            """ Create a member object form data item, return None if blocked or no usable key. """

            try:
                keys = sorted([(k['rfid_tag'], to_cet(dt_parse(k['end_timestamp'])))
                               for k in item['keys'] if not k['blocked'] and k['end_timestamp'] and k['rfid_tag']],
                              key=lambda x: x[1])
                
                if not keys:
                    return None
                
                rfid_tag, end_timestamp = keys[-1]
                
                return MakerAdminMember(
                    member_number=item['member_number'],
                    firstname=item['firstname'],
                    lastname=item['lastname'],
                    rfid_tag=rfid_tag,
                    end_timestamp=end_timestamp,
                )
            except ParseError as e:
                raise ValueError(f"Failed to parse timestamp: {str(e)}")
                
        return [ma for ma in (create_maker_admin(d) for d in data) if ma]
