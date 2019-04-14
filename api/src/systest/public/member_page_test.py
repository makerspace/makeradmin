from test_aid.obj import DEFAULT_PASSWORD_HASH
from test_aid.systest_base import SeleniumTest
from membership.models import Span


class Test(SeleniumTest):

    def get_member_key_boxes(self):
        return self.wait_for_elements(css=".member-key-box") # Contains info on membership length

    def test_view_member_shows_member_info(self):
        member = self.db.create_member(password=DEFAULT_PASSWORD_HASH)
        self.db.create_span(
            startdate=self.date(),
            enddate=self.date(30),
            type=Span.LABACCESS
        )

        self.login_member(member)
        
        self.browse_member_page()
        
        self.assertIn(member.firstname, self.wait_for_element(css="#content h2").text)
        
        member_key_boxes = self.get_member_key_boxes()
        self.assertEqual(2, len(member_key_boxes), "Info on special access should not appear if not active")
        self.assertIn("30 dagar till", " ".join([e.text for e in member_key_boxes]))
    
    def test_view_member_shows_special_access_when_added(self):
        member = self.db.create_member(password=DEFAULT_PASSWORD_HASH)
        self.db.create_span(
            startdate=self.date(),
            enddate=self.date(30),
            type=Span.SPECIAL_LABACESS
        )

        self.login_member(member)

        self.browse_member_page()

        member_key_boxes = self.get_member_key_boxes()
        self.assertEqual(3, len(member_key_boxes))
        self.assertIn("special", " ".join([e.text for e in member_key_boxes]))
