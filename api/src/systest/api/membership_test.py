from test_aid.systest_base import ApiTest
from test_aid.test_util import random_str


class Test(ApiTest):

    def test_new_member_does_not_have_labaccess_or_membership(self):
        member_id = self.api.create_member()['member_id']
        self.get(f"/membership/member/{member_id}/membership").expect(
            code=200,
            status="ok",
            data__has_labaccess=False,
            data__has_membership=False,
            data__labaccess_end=None,
            data__membership_end=None,
        )

    def test_add_membership_days_by_adding_days(self):
        member_id = self.api.create_member()['member_id']
        
        self.post(f"/membership/member/{member_id}/addMembershipDays",
                  {
                      "type": "membership",
                      "days": 1,
                      "default_start_date": self.date().isoformat(),
                      "creation_reason": random_str(),
                  }).expect(200)
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__has_membership=True,
                    data__labaccess_end=None,
                    data__membership_end=self.date(1).isoformat(),
                    )

    def test_add_membership_days_to_an_existing_span(self):
        member_id = self.api.create_member()['member_id']

        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "membership",
                      "startdate": self.date(0).isoformat(),
                      "enddate": self.date(1).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_membership=True,
                    data__membership_end=self.date(1).isoformat())
        
        self.post(f"/membership/member/{member_id}/addMembershipDays",
                  {
                      "type": "membership",
                      "days": 1,
                      "creation_reason": random_str(),
                  }).expect(200)
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__has_membership=True,
                    data__labaccess_end=None,
                    data__membership_end=self.date(2).isoformat(),
                    )

    def test_add_membership_days_by_adding_span(self):
        member_id = self.api.create_member()['member_id']
        
        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "membership",
                      "startdate": self.date().isoformat(),
                      "enddate": self.date(1).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__has_membership=True,
                    data__labaccess_end=None,
                    data__membership_end=self.date(days=1).isoformat(),
                    )

    def test_add_membership_span_in_the_past_does_not_give_membership(self):
        member_id = self.api.create_member()['member_id']
        
        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "membership",
                      "startdate": self.date(-40).isoformat(),
                      "enddate": self.date(-20).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__has_membership=False,
                    data__labaccess_end=None,
                    data__membership_end=self.date(days=-20).isoformat(),
                    )

    def test_add_membership_span_in_the_future_does_not_give_membership(self):
        member_id = self.api.create_member()['member_id']
        
        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "membership",
                      "startdate": self.date(20).isoformat(),
                      "enddate": self.date(40).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__has_membership=False,
                    data__labaccess_end=None,
                    data__membership_end=self.date(days=40).isoformat(),
                    )

    def test_add_membership_span_in_future_and_past_does_not_give_membership(self):
        member_id = self.api.create_member()['member_id']
        
        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "membership",
                      "startdate": self.date(-40).isoformat(),
                      "enddate": self.date(-20).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    )

        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "membership",
                      "startdate": self.date(20).isoformat(),
                      "enddate": self.date(40).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__has_membership=False,
                    data__labaccess_end=None,
                    data__membership_end=self.date(days=40).isoformat(),
                    )

    def test_add_labaccess_days_by_adding_days(self):
        member_id = self.api.create_member()['member_id']
        
        self.post(f"/membership/member/{member_id}/addMembershipDays",
                  {
                      "type": "labaccess",
                      "days": 1,
                      "default_start_date": self.date().isoformat(),
                      "creation_reason": random_str(),
                  }).expect(200)
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=True,
                    data__has_membership=False,
                    data__labaccess_end=self.date(1).isoformat(),
                    data__membership_end=None,
                    )

    def test_add_labaccess_days_to_an_existing_span(self):
        member_id = self.api.create_member()['member_id']

        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "labaccess",
                      "startdate": self.date().isoformat(),
                      "enddate": self.date(40).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=True,
                    data__labaccess_end=self.date(days=40).isoformat(),
                    )
        
        self.post(f"/membership/member/{member_id}/addMembershipDays",
                  {
                      "type": "labaccess",
                      "days": 1,
                      "default_start_date": self.date().isoformat(),
                      "creation_reason": random_str(),
                  }).expect(200)
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=True,
                    data__labaccess_end=self.date(41).isoformat(),
                    )

    def test_add_overlapping_span_does_still_give_labaccess(self):
        member_id = self.api.create_member()['member_id']

        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "labaccess",
                      "startdate": self.date(-40).isoformat(),
                      "enddate": self.date(10).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=True,
                    data__labaccess_end=self.date(days=10).isoformat(),
                    )

        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "labaccess",
                      "startdate": self.date(-10).isoformat(),
                      "enddate": self.date(40).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=True,
                    data__labaccess_end=self.date(days=40).isoformat(),
                    )

    def test_spans_before_and_after_today_does_not_give_labacess(self):
        member_id = self.api.create_member()['member_id']

        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "labaccess",
                      "startdate": self.date(-40).isoformat(),
                      "enddate": self.date(-10).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__labaccess_end=self.date(days=-10).isoformat(),
                    )

        self.post(f"/membership/span",
                  {
                      "member_id": member_id,
                      "type": "labaccess",
                      "startdate": self.date(10).isoformat(),
                      "enddate": self.date(40).isoformat(),
                      "creation_reason": random_str(),
                  }).is_ok()
        
        self.get(f"/membership/member/{member_id}/membership")\
            .expect(code=200,
                    status="ok",
                    data__has_labaccess=False,
                    data__labaccess_end=self.date(days=40).isoformat(),
                    )
