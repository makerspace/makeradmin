#
# Useful tip:
# When writing unit tests, add the code below inside a unit test to start a REPL inside the unit test to prototype things without having to restart all containers every single time
# import code
# code.InteractiveConsole(locals=locals()).interact()
#
from subprocess import call, check_output, STDOUT
from time import sleep
import unittest
import json
from datetime import datetime, timedelta

import requests
from requests import Response
import stripe
from decimal import Decimal
from requests import sessions


project_name = "test"
duplicatePurchaseRand = 0


def strip_entity_id(obj):
    copy = dict(obj)
    del copy["entity_id"]
    return copy


class APIGateway:
    def __init__(self, host: str, key: str, host_backend: str, host_public: str) -> None:
        self.host = self._ensure_protocol(host)
        self.host_backend = self._ensure_protocol(host_backend)
        self.host_public = self._ensure_protocol(host_public)
        self.auth_headers = {"Authorization": "Bearer " + key}

    def _get_headers(self, token):
        return self.auth_headers if token is None else {"Authorization": "Bearer " + token}

    @staticmethod
    def _ensure_protocol(host: str) -> str:
        if not host.startswith("http://") and not host.startswith("https://"):
            host = "http://" + host
        return host

    def get_public_url(self, path):
        host = self.host_public
        return f"{host}{path}"

    def get(self, path, payload=None, token=None) -> requests.Response:
        return requests.get(self.host + "/" + path, params=payload, headers=self._get_headers(token))

    def post(self, path, payload, token=None) -> requests.Response:
        return requests.post(self.host + "/" + path, json=payload, headers=self._get_headers(token))

    def put(self, path, payload, token=None) -> requests.Response:
        return requests.put(self.host + "/" + path, json=payload, headers=self._get_headers(token))

    def delete(self, path, token=None) -> requests.Response:
        return requests.delete(self.host + "/" + path, headers=self._get_headers(token))


def gateway_from_envfile(path):
    # Read the .env file
    with open(".env") as f:
        env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}
    host = env["HOST_BACKEND"]
    return APIGateway(host, env["API_BEARER"], env["HOST_BACKEND"], env["HOST_PUBLIC"])


class MemberDummies:
        def __init__(self, test, count):
            self.test = test
            self.count = count
            self.created_members = None

        def __enter__(self):
            member_template = {
                "email": "blah",
                "firstname": "test",
                "lastname": "testsson",
                "civicregno": "012345679",
                "company": "ACME",
                "orgno": "01234",
                "address_street": "Teststreet",
                "address_extra": "N/A",
                "address_zipcode": 1234,  # Note: not a string apparently
                "address_city": "Test Town",
                "address_country": "TS",  # Note: max length 2
                "phone": "0123456",
            }

            # Create a bunch of members
            members = []
            for i in range(self.count):
                m = dict(member_template)
                # The email needs to be completely unique in the database
                # even among previously deleted members
                m["email"] = "dummy_" + str(i)
                # Let php hash the password
                m["unhashed_password"] = True
                m["password"] = "passwd_" + str(i)
                members.append(m)

            self.created_members = []
            for member in members:
                response_member = dict(member)
                del response_member["password"]
                del response_member["unhashed_password"]
                created_member = self.test.post("membership/member", member, 201, expected_result={"status": "created", "data": response_member})["data"]
                # Makes many units tests easier because they can avoid having to compare the deleted_at field
                del created_member["deleted_at"]
                self.created_members.append(created_member)

            return zip(self.created_members, [member["password"] for member in members])

        def __exit__(self, type, value, traceback):
            for member in self.created_members:
                self.test.delete(f"membership/member/{member['member_id']}", 200, expected_result={"status": "deleted"})


class MakerAdminTest(unittest.TestCase):
    
    @classmethod
    def _wait_for_startup(cls):
        last_error = None
        for i in range(100):
            sleep(0.5)
            try:
                if cls.gateway.get("membership/member").ok:
                    # Extra sleep for safety (technically this method only checks for if the membership service has
                    # started)
                    sleep(0.5)
                    return
            except Exception as e:
                last_error = str(e)
                # Ignore any exceptions
                # Until the services are up and running the connection may fail in any number of ways

        raise Exception(f"Timeout while waiting for services to start, last_error: {last_error}")

    def assertSubset(self, subset, obj):
        if isinstance(subset, list):
            self.assertIsInstance(obj, list)
            self.assertEqual(len(subset), len(obj))
            for a, b in zip(subset, obj):
                self.assertSubset(a, b)
            return

        if not isinstance(subset, dict):
            self.assertNotIsInstance(obj, dict)
            self.assertEqual(subset, obj)
            return

        for key in subset.keys():
            self.assertIn(key, obj)
            self.assertSubset(subset[key], obj[key])

    def assertResponseSubset(self, response: Response, status_code: int, json_subset: dict):
        try:
            self.assertEqual(response.status_code, status_code)
            response_json = response.json()
            self.assertSubset(json_subset, response_json)
            return response_json
        except:
            print("Error when processing response: " + str(response.status_code) + " " + response.text)
            print("Expected the response to be a superset of\n" + json.dumps(json_subset, indent=4))
            raise

    @classmethod
    def setUpClass(cls):
        # Remove any earlier running containers
        call(["docker-compose", "-p", project_name, "down"])

        # Remove previous database
        call(["docker", "volume", "rm", f"{project_name}_dbdata"])

        # Create all test containers
        call(["docker-compose", "-p", project_name, "up", "--no-start"])

        # Initialize the database
        call(["python3", "db_init.py", "--project-name", project_name])

        # Start all test containers
        call(["docker-compose", "-p", project_name, "-f", "docker-compose.yml", "-f", "docker-compose.test.yml", "up", "-d"])

        cls.gateway = gateway_from_envfile(".env")
        # Test backend uses a different port than the one in the .env file
        cls.gateway.host = "http://localhost:9010"

        print("Waiting for services to start...")
        MakerAdminTest._wait_for_startup()

        print("Services have started")

        # Read the .env file
        with open(".env") as f:
            env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}

        stripe.api_key = env["STRIPE_PUBLIC_KEY"]

        # Removes some annoying warning messages logged during runtime
        cls.requests_session = sessions.Session()
        client = stripe.http_client.RequestsClient(session=cls.requests_session)
        stripe.default_http_client = client

    @classmethod
    def tearDownClass(cls):
        cls.requests_session.close()
        print("\nStopping containers...")
        # check_output(["docker-compose", "-p", project_name, "stop", "-t", "60"], stderr=STDOUT)
        check_output(["docker-compose", "-p", project_name, "down"], stderr=STDOUT)

    def get(self, url, status_code=200, *, expected_result={}, token=None):
        return self.assertResponseSubset(self.gateway.get(url, token), status_code, expected_result)

    def delete(self, url, status_code=200, *, expected_result={}, token=None):
        return self.assertResponseSubset(self.gateway.delete(url, token), status_code, expected_result)

    def post(self, url, payload={}, status_code=200, *, expected_result={}, token=None):
        return self.assertResponseSubset(self.gateway.post(url, payload, token), status_code, expected_result)

    def put(self, url, payload={}, status_code=200, *, expected_result={}, token=None):
        return self.assertResponseSubset(self.gateway.put(url, payload, token=None), status_code, expected_result)

