import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '../servicebase_python'))
import service
from service import eprint
from datetime import datetime, timedelta
import json
import re


gateway = service.gateway_from_envfile(".env")

keys = gateway.get("keys").json()["data"]
members = gateway.get("membership/member").json()["data"]

def confirm_post(gateway_, route_, data_):
    print(json.dumps(data_, ensure_ascii=False, indent=2))
    i = ""
    while i not in {'y', 'yes', 'n', 'no'}:
        i = input(f"Confirm span (yes/no?): ").lower()
    if i in {'y', 'yes'}:
        r = gateway_.post(route_, data_)
        assert r.ok, r.text

matching_members = []
for key in keys:
    member_number = key["title"]
    member_number = member_number.replace("#", "").strip()
    member_number = int(member_number)

    matching = [m for m in members if m["member_number"] == member_number]
    if len(matching) == 0:
        eprint(f"No matching member for key {key['tagid']} with title {member_number}")
        exit(1)
    elif len(matching) > 1:
        eprint(f"Multiple matching members for key {key['tagid']} with title {member_number}")
        exit(1)

    matching_members.append(matching[0])


for key, member in zip(keys, matching_members):
    key["member_id"] = member["member_id"]
    print(key)
    print("Creating key " + key["tagid"])
    if key["status"] == "active":
        start = key["startdate"]
        end = key["enddate"]

        # If the key does not have a start date, set the current date as the start date
        if start is None:
            start = service.format_datetime(datetime.now())

        span = {
            "member_id": member["member_id"],
            "startdate": start,
            "enddate": key["enddate"],
            "type": "labaccess",
            "creation_reason": "migrated key:" + str(key['tagid'])
        }

        if end is None:
            print(json.dumps(key,ensure_ascii=False, indent=2))
            add_special = ""
            while add_special not in {'y', 'yes', 'n', 'no'}:
                add_special = input(f"Add special lab access to member {key['member_id']} (y/n)? ").lower()
            if add_special in {'y', 'yes'}:
                now = datetime.now()
                special_end = datetime(year=now.year, month=4, day=1)
                if special_end < now:
                    special_end = datetime(year=now.year+1, month=4, day=1)
                special_span = {
                    "member_id": member["member_id"],
                    "startdate": start,
                    "enddate": service.format_datetime(special_end),
                    "type": "special_labaccess",
                    "creation_reason": "migrated"
                }
                confirm_post(gateway, f"membership/member/{member['member_id']}/addMembershipSpan", special_span)
            print(json.dumps(key, ensure_ascii=False, indent=2))
            add_lab = None
            while add_lab is None:
                s = input(f"Add lab access to member {key['member_id']} (enddate(eg 2018-10-25)/no)? ").lower()
                add_lab = re.match("((?:\d{2}|\d{4})-\d{2}-\d{2}|n|no)", s)
            if add_lab.group(0) not in {'n', 'no'}:
                # Valid date was entered
                lab_end = datetime.strptime('20'+add_lab.group(1) if len(add_lab.group(1)) == 8 else add_lab.group(1),'%Y-%m-%d')
                span['enddate'] = service.format_datetime(lab_end)
                confirm_post(gateway, f"membership/member/{member['member_id']}/addMembershipSpan", span)
        else:
            r = gateway.post(f"membership/member/{member['member_id']}/addMembershipSpan", span)
            assert r.ok, r.text

    r = gateway.post(f"membership/key", key)
    assert r.ok, r.text
