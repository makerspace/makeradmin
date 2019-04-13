from test_aid.obj import DEFAULT_PASSWORD_HASH
from test_aid.systest_base import SeleniumTest


class Test(SeleniumTest):

    def test_view_member_shows_member_info(self):
        member = self.db.create_member(password=DEFAULT_PASSWORD_HASH)
        self.db.create_span(
            startdate=self.date(),
            enddate=self.date(30)
        )

        self.login_member(member)
        
        self.browse_member_page()
        
        self.assertIn(member.firstname, self.wait_for_element(css="#content h2").text)
        
        self.assertIn("30 dagar till", " ".join([e.text for e in self.wait_for_elements(css=".member-key-box")]))
