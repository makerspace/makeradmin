import os
import unittest

from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote import webdriver as remote
from selenium.webdriver.chrome import webdriver as chrome


webdriver_type = os.environ.get('WEBDRIVER_TYPE', 'CHROME')
keep_browser = os.environ.get('KEEP_BROWSER')
test_mode = os.environ.get('TEST_MODE', 'DEV')


def create_webdriver():
    if webdriver_type == 'CHROME':
        return chrome.WebDriver()
    
    if webdriver_type == 'REMOTE_CHROME':
        return remote.WebDriver(command_executor='http://selenium:4444/wd/hub',
                                desired_capabilities=DesiredCapabilities.CHROME)
    
    raise Exception(f"bad webdriver type {webdriver_type}")


class TestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        if test_mode == 'DEV':
            self.admin_url = 'http://localhost:8009'
            self.public_url = 'http://localhost:8011'
            self.api = 'http://localhost:8010'
            
        elif test_mode == 'DOCKER':
            self.admin_url = 'http://admin:80'
            self.public_url = 'http://public:80'
            self.api = 'http://api-gateway:80'
            
        else:
            raise Exception(f"unknown test_mode {test_mode}")


class SeleniumTest(TestCase):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.webdriver = create_webdriver()
    
    @classmethod
    def tearDownClass(self):
        if not keep_browser:
            self.webdriver.close()
        super().tearDownClass()
