import os
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote import webdriver as remote
from selenium.webdriver.chrome import webdriver as chrome

from library.base import TestCaseBase

webdriver_type = os.environ.get('WEBDRIVER_TYPE', 'CHROME')
keep_browser = os.environ.get('KEEP_BROWSER')


def create_webdriver():
    if webdriver_type == 'CHROME':
        return chrome.WebDriver()
    
    if webdriver_type == 'REMOTE_CHROME':
        return remote.WebDriver(command_executor='http://selenium:4444/wd/hub',
                                desired_capabilities=DesiredCapabilities.CHROME)
    
    raise Exception(f"bad webdriver type {webdriver_type}")


class SeleniumTest(TestCaseBase):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.webdriver = create_webdriver()
    
    @classmethod
    def tearDownClass(self):
        if not keep_browser:
            self.webdriver.close()
        super().tearDownClass()


