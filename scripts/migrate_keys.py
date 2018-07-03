import sys
import os
import pymysql
sys.path.insert(1, os.path.join(sys.path[0], '../servicebase_python'))

import service

gateway = service.gateway_from_envfile(".env")

keys = gateway.get("keys").json()["data"]
members = gateway.get("membership/member").json()["data"]

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
	member = matching[0]
	key["member_id"] = member["member_id"]
	gateway.post(f"membership/key", key)
