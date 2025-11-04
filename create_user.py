#!/usr/bin/env python3
import argparse
import os
import sys
from typing import Optional

import requests
from dotenv import dotenv_values

env = dotenv_values()

# Ugly
sys.path.append(os.path.join(os.path.dirname(__file__), "backend/src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "api/src"))

from basic_types.enums import PriceLevel

# import backend_service

headers = {
    "Authorization": f"Bearer {env.get('TEST_SERVICE_TOKEN')}",
}
api_url = env.get("HOST_BACKEND")

if not api_url.startswith("http"):
    api_url = "http://" + api_url


def post(url, payload):
    print(payload)
    return requests.post(f"{api_url}/{url}", headers=headers, json=payload)


def get(url):
    return requests.get(f"{api_url}/{url}", headers=headers)


def create_user(first_name: str, last_name: str, email: str, user_type: str, password: Optional[str]):
    # gateway = backend_service.gateway_from_envfile(".env")

    try:
        payload = {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
            "pending_activation": False,
            "price_level": PriceLevel.Normal.value,
        }
        if password is not None:
            payload["unhashed_password"] = password

        # r = gateway.post("membership/member", payload=payload)
        r = post("membership/member", payload=payload)
    except Exception as e:
        print("Could not connect to the membership service. Are you sure makeradmin is running?")
        print(e)
        exit(1)

    assert r.ok, r.text
    user = r.json()["data"]

    if user_type == "admin":
        admin_group_id = [g["group_id"] for g in get("membership/group").json()["data"] if g["name"] == "admins"][0]
        r = post("membership/member/" + str(user["member_id"]) + "/groups/add", payload={"groups": [admin_group_id]})
        assert r.ok, r.text

    return user


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new MakerAdmin user")
    parser.add_argument("--first-name", help="First name of the user", required=True)
    parser.add_argument("--last-name", help="Last name of the user", required=True)
    parser.add_argument("--email", help="Email of the user", required=True)
    parser.add_argument("--type", choices=["user", "admin"], required=True)
    parser.add_argument("--password", help="Password (only relevant for admins)", required=False)

    args = parser.parse_args()
    create_user(args.first_name, args.last_name, args.email, args.type, args.password)
    print("Done")
