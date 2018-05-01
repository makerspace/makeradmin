from collections import namedtuple

import requests

MemberInfo = namedtuple('MemberInfo', [
    'member_id',      # int for debugging
    'member_number',  # int
    'firstname',      # string
    'lastname',       # string
    'key_id',         # int for debugging
    'rfid_tag',       # string
    'status',         # bool
    'end_timestamp',  # string timestamp in zulu
])


# TODO Write tests for this when we know how it should work.
def fetch_member_info(url, auth):
    """ Fetch and return list of MemberInfo, raises. """
    
    r = requests.get(url, headers=auth.get_headers())
    return [MemberInfo(**m) for m in r.json()]
