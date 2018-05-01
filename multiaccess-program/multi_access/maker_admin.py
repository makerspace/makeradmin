from collections import namedtuple

import requests

MakerAdminMember = namedtuple('MemberInfo', [
    'member_id',      # int for debugging
    'member_number',  # int
    'firstname',      # string
    'lastname',       # string
    'key_id',         # int for debugging
    'rfid_tag',       # string
    'status',         # bool TODO what does false and true mean? do not handle this at the moment
    'end_timestamp',  # string timestamp in zulu
])


# TODO Write tests for this when we know how it should work.
def fetch_maker_admin_members(url, auth):
    """ Fetch and return list of MakerAdminMember, raises exception on error. """
    r = requests.get(url, headers=auth.get_headers())
    return [MakerAdminMember(**m) for m in r.json()]
