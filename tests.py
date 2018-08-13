from subprocess import call, check_output, STDOUT
from time import sleep
import servicebase_python.service
import unittest
import json
from requests import Response

project_name = "test"


def strip_entity_id(obj):
    copy = dict(obj)
    del copy["entity_id"]
    return copy


class MakerAdminTest(unittest.TestCase):
    @classmethod
    def _wait_for_startup(cls):
        for i in range(100):
            sleep(0.5)
            try:
                if cls.gateway.get("membership/member").ok:
                    # Extra sleep for safety (technically this method only checks for if the membership service has started)
                    sleep(0.5)
                    return
            except:
                # Ignore any exceptions
                # Until the services are up and running the connection may fail in any number of ways
                pass

        raise Exception("Timeout while waiting for services to start")

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

        cls.gateway = servicebase_python.service.gateway_from_envfile(".env")
        # Test backend uses a different port than the one in the .env file
        cls.gateway.host = "localhost:9010"

        print("Waiting for services to start...")
        MakerAdminTest._wait_for_startup()

        print("Services have started")

    @classmethod
    def tearDownClass(cls):
        print("\nStopping containers...")
        check_output(["docker-compose", "-p", project_name, "down"], stderr=STDOUT)

    def get(self, url, status_code=200, *, expected_result={}):
        return self.assertResponseSubset(self.gateway.get(url), status_code, expected_result)

    def delete(self, url, status_code=200, *, expected_result={}):
        return self.assertResponseSubset(self.gateway.delete(url), status_code, expected_result)

    def post(self, url, payload={}, status_code=200, *, expected_result={}):
        return self.assertResponseSubset(self.gateway.post(url, payload), status_code, expected_result)

    def put(self, url, payload={}, status_code=200, *, expected_result={}):
        return self.assertResponseSubset(self.gateway.put(url, payload), status_code, expected_result)

    def test_member(self):
        ''' Test various things to do with members '''
        previous_members = self.get(f"membership/member", 200)["data"]

        member = {
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
        new_member = self.post("membership/member", member, 201, expected_result={"status": "created", "data": member})["data"]
        self.assertIn("member_id", new_member)
        self.assertIn("member_number", new_member)

        self.post("membership/member", member, 422, expected_result={"status": "error", "column": "email"})
        self.get(f"membership/member/{new_member['member_id']}", 200, expected_result={"data": member})

        member2 = dict(member)
        member2["email"] = "blah2"
        new_member2 = self.post("membership/member", member2, 201, expected_result={"status": "created", "data": member2})["data"]

        self.assertNotEqual(new_member["member_number"], new_member2["member_number"])

        for key in member.keys():
            val = member[key]
            if isinstance(val, int):
                val ^= 5324
            elif isinstance(val, str):
                # Modify the string without changing the length (many fields are length limited)
                s = ""
                for c in val:
                    s += chr(ord(c) + 13)
                val = s
            member[key] = val

        self.put(f"membership/member/{new_member['member_id']}", member, 200, expected_result={"status": "updated", "data": member})
        new_member = self.get(f"membership/member/{new_member['member_id']}", 200, expected_result={"data": member})["data"]

        for m in [new_member, new_member2]:
            self.delete(f"membership/member/{m['member_id']}", 200, expected_result={"status": "deleted"})
            # Note that deleted members still show up when explicitly accessed, but they should not show up in lists (this is checked for below)
            self.get(f"membership/member/{m['member_id']}", 200, expected_result={"data": m})

        self.get(f"membership/member", 200, expected_result={"data": previous_members})

    def test_groups(self):
        ''' Test various things to do with groups '''
        previous_groups = self.get(f"membership/group", 200)["data"]

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
        for i in range(10):
            m = dict(member_template)
            m["email"] = "email_" + str(i)
            members.append(m)

        created_members = [
            self.post("membership/member", member, 201, expected_result={"status": "created", "data": member})["data"]
            for member in members
        ]

        groups = [{
            "name": "science_group" + str(i),
            "title": "Aperture Science Volounteer Group",
            "description": "Volounteers for being exposed to neurotoxin",
        } for i in range(10)]

        created_groups = [
            self.post("membership/group", group, 201, expected_result={"status": "created", "data": group})["data"]
            for group in groups
        ]

        # Make sure the get method returns the same result as the post method
        for group in created_groups:
            self.get(f"membership/group/{group['group_id']}", 200, expected_result={"data": group})

        # List all groups
        # Inconsistency: list views do not include entity_id
        self.get(f"membership/group", 200, expected_result={"data": previous_groups + list(map(strip_entity_id, created_groups))})

        for member, group in zip(created_members, created_groups):
            member_id = member["member_id"]
            group_id = group["group_id"]

            self.post(f"membership/member/{member_id}/groups/add", {"groups": [group_id]}, 200, expected_result={"status": "ok"})

            # Inconsistency: list views do not include entity_id
            group2 = strip_entity_id(group)

            member2 = strip_entity_id(member)

            # Make sure the member has been added to the group
            self.get(f"membership/member/{member_id}/groups", 200, expected_result={"data": [group2]})
            self.get(f"membership/group/{group_id}/members", 200, expected_result={"data": [member2]})

            # Remove the member from the group
            self.post(f"membership/member/{member_id}/groups/remove", {"groups": [group_id]}, 200, expected_result={"status": "ok"})

            # Make sure the member has been removed from the group
            self.get(f"membership/member/{member_id}/groups", 200, expected_result={"data": []})

        for group in created_groups:
            self.delete(f"membership/group/{group['group_id']}", 200, expected_result={"status": "deleted"})
            # Note that deleted groups still show up when explicitly accessed, but they should not show up in lists (this is checked for below)
            self.get(f"membership/group/{group['group_id']}", 200, expected_result={"data": group})

        for member in created_members:
            self.delete(f"membership/member/{member['member_id']}", 200, expected_result={"status": "deleted"})

        # Make sure all groups have been deleted
        self.get(f"membership/group", 200, expected_result={"data": previous_groups})
