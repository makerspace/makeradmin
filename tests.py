#
# Useful tip:
# When writing unit tests, add the code below inside a unit test to start a REPL inside the unit test to prototype things without having to restart all containers every single time
# import code
# code.InteractiveConsole(locals=locals()).interact()
#
from subprocess import call, check_output, STDOUT
from time import sleep
import servicebase_python.service
import unittest
import json
from datetime import datetime, timedelta
from requests import Response
import stripe

project_name = "test"


def strip_entity_id(obj):
    copy = dict(obj)
    del copy["entity_id"]
    return copy


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
            for i in range(10):
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
                self.created_members.append(self.test.post("membership/member", member, 201, expected_result={"status": "created", "data": response_member})["data"])

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

        cls.gateway = servicebase_python.service.gateway_from_envfile(".env")
        # Test backend uses a different port than the one in the .env file
        cls.gateway.host = "http://localhost:9010"

        print("Waiting for services to start...")
        MakerAdminTest._wait_for_startup()

        print("Services have started")

        # Read the .env file
        with open(".env") as f:
            env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}

        stripe.api_key = env["STRIPE_PUBLIC_KEY"]

    @classmethod
    def tearDownClass(cls):
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

        with MemberDummies(self, 10) as created_members:
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

            for (member, password), group in zip(created_members, created_groups):
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

            # Make sure all groups have been deleted
            self.get(f"membership/group", 200, expected_result={"data": previous_groups})

    def test_membership(self):
        with MemberDummies(self, 5) as created_members:

            for i, (member, password) in enumerate(created_members):
                member_id = member['member_id']
                self.get(f"/membership/member/{member_id}/membership", 200, expected_result={
                    "status": "ok",
                    "data": {
                        "has_labaccess": False,
                        "has_membership": False,
                        "labaccess_end": None,
                        "membership_end": None
                    }
                })

                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "labaccess", "days": 10, "creation_reason": f"test_{member_id}"}, 200, expected_result={
                    "status": "ok",
                    "data": {
                        "has_labaccess": True,
                        "has_membership": False,
                        "labaccess_end": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
                        "membership_end": None
                    }
                })

                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "labaccess", "days": 15, "creation_reason": f"test2_{member_id}"}, 200, expected_result={
                    "status": "ok",
                    "data": {
                        "has_labaccess": True,
                        "has_membership": False,
                        "labaccess_end": (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d"),
                        "membership_end": None
                    }
                })

                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "labaccess", "days": 15, "creation_reason": f"test2_{member_id}"}, 200, expected_result={
                    "status": "ok",
                    "data": {
                        "has_labaccess": True,
                        "has_membership": False,
                        "labaccess_end": (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d"),
                        "membership_end": None
                    }
                })

                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "labaccess", "days": 14, "creation_reason": f"test2_{member_id}"}, 400, expected_result={
                    "status": "error",
                })

                self.post(f"/membership/member/{member_id}/addMembershipSpan", {
                        "type": "membership",
                        "startdate": (datetime.now() + timedelta(days=i-2)).strftime("%Y-%m-%d"),
                        "enddate": (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d"),
                        "creation_reason": f"test3_{member_id}"
                    },
                    200, expected_result={
                        "status": "ok",
                        "data": {
                            "has_labaccess": True,
                            "has_membership": i <= 2,
                            "labaccess_end": (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d"),
                            "membership_end": (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
                        }
                    }
                )

                self.post(f"/membership/member/{member_id}/addMembershipSpan", {
                        "type": "special_labaccess",
                        "startdate": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
                        "enddate": (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d"),
                        "creation_reason": f"test4_{member_id}"
                    },
                    200, expected_result={
                        "status": "ok",
                        "data": {
                            "has_labaccess": True,
                            "has_membership": i <= 2,
                            "labaccess_end": (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d"),
                            "membership_end": (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
                        }
                    }
                )

                self.post(f"/membership/member/{member_id}/addMembershipSpan", {
                        "type": "special_labaccess",
                        "startdate": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
                        "enddate": (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d"),
                        "creation_reason": f"test4_{member_id}"
                    },
                    200, expected_result={
                        "status": "ok",
                        "data": {
                            "has_labaccess": True,
                            "has_membership": i <= 2,
                            "labaccess_end": (datetime.now() + timedelta(days=40)).strftime("%Y-%m-%d"),
                            "membership_end": (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
                        }
                    }
                )

                self.post(f"/membership/member/{member_id}/addMembershipSpan", {
                        "type": "special_labaccess",
                        "startdate": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
                        "enddate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                        "creation_reason": f"test4_{member_id}"
                    },
                    400, expected_result={
                        "status": "error",
                    }
                )

                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "labaccess", "days": -1, "creation_reason": f"test5_{member_id}"}, 400, expected_result={"status": "error"})
                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "lulz", "days": 10, "creation_reason": f"test6_{member_id}"}, 400, expected_result={"status": "error"})
                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "labaccess", "days": 10, "creation_reason": None}, 400, expected_result={"status": "error"})
                self.post(f"/membership/member/{member_id}/addMembershipDays", {"type": "labaccess", "days": 10}, 400, expected_result={"status": "error"})

    def test_purchase(self):
        if not stripe.api_key:
            return
        with MemberDummies(self, 2) as created_members:
            for i, (member, password) in enumerate(created_members):
                member_id = member['member_id']

                category = {
                    "name": "Blah"
                }
                created_category = self.post(f"/webshop/category", category, 200, expected_result={"status": "created", "data": category})["data"]

                product1 = {
                    "name": "Meh",
                    "price": "12.30",
                    "description": "This is a description",
                    "unit": "st",
                    "smallest_multiple": 1,
                    "filter": None,
                    "category_id": created_category["id"],
                }
                created_product1 = self.post(f"/webshop/product", product1, 200, expected_result={"status": "created", "data": product1})["data"]

                product2 = {
                    "name": "Meh2",
                    "price": "1.20",
                    "description": "This is not a description",
                    "unit": "mm",
                    "smallest_multiple": 100,
                    "filter": None,
                    "category_id": created_category["id"],
                }
                created_product2 = self.post(f"/webshop/product", product2, 200, expected_result={"status": "created", "data": product2})["data"]

                token = self.post(f"/oauth/token", {"grant_type": "password", "username": member["email"], "password": password}, 200)["access_token"]

                STRIPE_TEST_CARD = {
                    "number": '4242424242424242',
                    "exp_month": 12,
                    "exp_year": 2019,
                    "cvc": '123'
                }

                source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_TEST_CARD).id)
                purchase = {
                    "cart": [
                        {
                            "id": created_product1["id"],
                            "count": 3,
                        },
                        {
                            "id": created_product2["id"],
                            "count": 100,
                        }
                    ],
                    "expectedSum": "156.9",
                    "duplicatePurchaseRand": i*100 + 0,
                    "stripeSource": source.id,
                    "stripeThreeDSecure": source["card"]["three_d_secure"]
                }

                # Make a valid purchase
                transaction_id = self.post(f"/webshop/pay", purchase, 200, token=token, expected_result={"status": "ok"})["data"]["transaction_id"]

                # Verify the transaction
                self.get(f"/webshop/transaction/{transaction_id}", 200, token=token, expected_result={
                    "status": "ok",
                    "data": {
                        "amount": "156.90",
                        "member_id": member_id,
                        "status": "completed"
                    },
                })

                # Verify the contents
                self.get(f"/webshop/transaction/{transaction_id}/content", 200, token=token, expected_result={
                    "status": "ok",
                    "data": [
                        {
                            "amount": "36.90",
                            "count": 3,
                            "product_id": created_product1["id"],
                            "product_name": "Meh"
                        },
                        {
                            "amount": "120.00",
                            "count": 100,
                            "product_id": created_product2["id"],
                            "product_name": "Meh2"
                        }
                    ]
                })

                # Make some invalid purchases

                source = stripe.Source.create(type="card", token=stripe.Token.create(card=STRIPE_TEST_CARD).id)

                # Product 2 can only be purchased in multiples of 100
                purchase = {
                    "cart": [
                        {
                            "id": created_product2["id"],
                            "count": 7,
                        }
                    ],
                    "expectedSum": "8.40",
                    "duplicatePurchaseRand": i*100 + 1,
                    "stripeSource": source.id,
                    "stripeThreeDSecure": source["card"]["three_d_secure"]
                }
                self.post(f"/webshop/pay", purchase, 400, token=token, expected_result={"status": "InvalidItemCountMultiple"})

                # Invalid expected sum
                purchase = {
                    "cart": [
                        {
                            "id": created_product1["id"],
                            "count": 3,
                        },
                        {
                            "id": created_product2["id"],
                            "count": 100,
                        }
                    ],
                    "expectedSum": "19.20",
                    "duplicatePurchaseRand": i*100 + 2,
                    "stripeSource": source.id,
                    "stripeThreeDSecure": source["card"]["three_d_secure"]
                }
                self.post(f"/webshop/pay", purchase, 400, token=token, expected_result={"status": "NonMatchingSums"})

                # Negative amounts
                purchase = {
                    "cart": [
                        {
                            "id": created_product1["id"],
                            "count": -3,
                        }
                    ],
                    "expectedSum": "19.20",
                    "duplicatePurchaseRand": i*100 + 3,
                    "stripeSource": source.id,
                    "stripeThreeDSecure": source["card"]["three_d_secure"]
                }
                self.post(f"/webshop/pay", purchase, 400, token=token, expected_result={"status": "NonNegativeItemCount"})
