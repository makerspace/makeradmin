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


class MakerAdminClient(object):
    
    def __init__(self, base_url=None):
        self.base_url = base_url
    
    # TODO Write tests for when this it is known it should work.
    def fetch_members(self, ui):
        """ Fetch and return list of MakerAdminMember, raises exception on error. """
        url = self.base_url + '/members'
        ui.info__progress(f"getting member list from {url}")
        
        r = requests.get(url)
        res = [MakerAdminMember(**m) for m in r.json()]
        
        ui.info__progress(f"got {len(res)} members")
        
        return res
