#!/usr/bin/python3
import requests
import argparse

# Read the .env file
env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in open(".env").read().split('\n'))}

# TODO: Need to read this port value from somewhere
port = 8010


class APIGateway:
    def __init__(self, host, key):
        self.host = host
        self.key = key

    def get(self, path, payload=None):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.get('http://' + self.host + "/" + path, params=payload, headers=headers)

    def post(self, path, payload):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.post('http://' + self.host + "/" + path, json=payload, headers=headers)

    def put(self, path, payload):
        headers = {"Authorization": "Bearer " + self.key}
        return requests.put('http://' + self.host + "/" + path, json=payload, headers=headers)


gateway = APIGateway("localhost:" + str(port), env["API_BEARER"])

parser = argparse.ArgumentParser(description='Create a new MakerAdmin user')
parser.add_argument("--first-name", help="First name of the user", required=True)
parser.add_argument("--last-name", help="Last name of the user", required=True)
parser.add_argument("--email", help="Email of the user", required=True)
parser.add_argument("--type", choices=["user", "admin"], required=True)
parser.add_argument("--password", help="Password (only relevant for admins)", required=False)

args = parser.parse_args()

try:
    payload = {
        "email": args.email,
        "firstname": args.first_name,
        "lastname": args.last_name,
        "unhashed_password": True  # Let php hash the password
    }
    if args.password is not None:
        payload["password"] = args.password

    r = gateway.post("membership/member", payload=payload)
except Exception as e:
    print("Could not connect to the membership service. Are you sure makeradmin is running?")
    print(e)
    exit(1)

assert r.ok, r.text
user = r.json()["data"]

if args.type == "admin":
    admin_group_id = [g["group_id"] for g in gateway.get("membership/group").json()["data"] if g["name"] == "admins"][0]
    r = gateway.post("membership/member/" + str(user["member_id"]) + "/groups/add", payload={
        "groups": [admin_group_id]
    })
    assert r.ok, r.text

print("Done")
