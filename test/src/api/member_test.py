from lib.base import ApiTest
from lib.factory import MemberFactory


class Test(ApiTest):
    
    def test_create_member(self):
        member = MemberFactory()
        
        member_id, member_number = self\
            .post("membership/member", json=member)\
            .expect(code=201, data=member)\
            .get('data__member_id', 'data__member_number')

        self.assertTrue(member_id)
        self.assertTrue(member_number)
        
        self.get(f"membership/member/{member_id}").expect(code=200, data=member, data__member__member_id=member_id)

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
            self.get(f"membership/member/{m['member_id']}", 200, expected_result={"data": {k: m[k] for k in m if k not in {"deleted_at"}}})

        self.get(f"membership/member", 200, expected_result={"data": previous_members})


pass
