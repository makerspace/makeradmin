from library.selenium import SeleniumTest


class Test(SeleniumTest):
    
    def test_noop(self):
        self.webdriver.get(self.admin_url)
        self.webdriver.save_screenshot("/tmp/fil.png")
