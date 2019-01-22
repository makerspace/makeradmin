#!/usr/bin/env python3
import argparse
import sys
import os
from typing import Optional

# Ugly
sys.path.append(os.path.join(os.path.dirname(__file__), "backend/src"))

import backend_service

def create_user(first_name: str, last_name: str, email: str, user_type: str, password: Optional[str]):
    gateway = backend_service.gateway_from_envfile(".env")


    try:
        payload = {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
        }
        if password is not None:
            payload["unhashed_password"] = password

        r = gateway.post("membership/member", payload=payload)
    except Exception as e:
        print("Could not connect to the membership service. Are you sure makeradmin is running?")
        print(e)
        exit(1)

    assert r.ok, r.text
    user = r.json()["data"]

    if user_type == "admin":
        admin_group_id = [g["group_id"] for g in gateway.get("membership/group").json()["data"] if g["name"] == "admins"][0]
        r = gateway.post("membership/member/" + str(user["member_id"]) + "/groups/add", payload={
            "groups": [admin_group_id]
        })
        assert r.ok, r.text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a new MakerAdmin user')
    parser.add_argument("--first-name", help="First name of the user", required=True)
    parser.add_argument("--last-name", help="Last name of the user", required=True)
    parser.add_argument("--email", help="Email of the user", required=True)
    parser.add_argument("--type", choices=["user", "admin"], required=True)
    parser.add_argument("--password", help="Password (only relevant for admins)", required=False)

    args = parser.parse_args()
    create_user(args.first_name, args.last_name, args.email, args.type, args.password)
    print("Done")
