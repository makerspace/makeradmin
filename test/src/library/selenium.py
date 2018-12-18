import os
import sys
from logging import getLogger

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote import webdriver as remote
from selenium.webdriver.chrome import webdriver as chrome
from selenium.webdriver.support.wait import WebDriverWait

from library.api import ApiTest
from library.test_config import KEEP_BROWSER, WEBDRIVER_TYPE, SELENIUM_SCREENSHOT_DIR
from library.util import retry, SELENIUM_BASE_TIMEOUT, SLEEP

logger = getLogger('makeradmin')


def create_webdriver():
    if WEBDRIVER_TYPE == 'CHROME':
        return chrome.WebDriver()
    
    if WEBDRIVER_TYPE == 'REMOTE_CHROME':
        return remote.WebDriver(command_executor='http://selenium:4444/wd/hub',
                                desired_capabilities=DesiredCapabilities.CHROME)
    
    raise Exception(f"bad webdriver type {WEBDRIVER_TYPE}")


class SeleniumTest(ApiTest):
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.webdriver = create_webdriver()
        
    def tearDown(self):
        if self.this_test_failed():
            if not os.path.exists(SELENIUM_SCREENSHOT_DIR):
                os.makedirs(SELENIUM_SCREENSHOT_DIR)
                os.chmod(SELENIUM_SCREENSHOT_DIR, 0o777)
            filename = f'{SELENIUM_SCREENSHOT_DIR}/{self.id()}--{self.now.strftime("%Y-%m-%dT%H-%M-%S")}'
            
            print(f"saving screenshot to {filename}.png", file=sys.stderr)
            try:
                self.webdriver.save_screenshot(filename + '.png')
                with open(filename + '.html', 'w') as w:
                    w.write(self.webdriver.page_source)
                with open(filename + '.url', 'w') as w:
                    w.write(self.webdriver.current_url)
                with open(filename + '.console', 'w') as w:
                    w.write(repr(self.webdriver.get_log('browser')))
            except Exception as e:
                print(f"failed to save screenshot: {str(e)}", file=sys.stderr)
        
        super().tearDown()
    
    @classmethod
    def tearDownClass(self):
        if not KEEP_BROWSER:
            self.webdriver.close()
        super().tearDownClass()

    def wait(self, cond=None, ret=None, timeout=SELENIUM_BASE_TIMEOUT, sleep=SLEEP):
        WebDriverWait(self.webdriver, timeout, sleep).until(cond)

    def wait_for_page(self, title=None):
        self.wait(lambda w: w.execute_script('return (document.readyState == "complete");'))
        if title:
            self.wait(lambda w: w.title == title)

    def login_member(self, member=None):
        token = self.api.login_member(member)
        self.webdriver.get(f"{self.public_url}/member/login/{token}")

    def wait_for_element(self, id=None, name=None, tag=None, css=None, xpath=None,
                         timeout=SELENIUM_BASE_TIMEOUT, sleep=SLEEP):
        if id:
            def get():
                return self.webdriver.find_element_by_id(id)
        elif name:
            def get():
                return self.webdriver.find_element_by_name(name)
        elif tag:
            def get():
                return self.webdriver.find_element_by_tag_name(tag)
        elif css:
            def get():
                return self.webdriver.find_element_by_css_selector(css)
        elif xpath:
            def get():
                return self.webdriver.find_element_by_xpath(xpath)
        else:
            raise Exception("missing parameter")
        
        return retry(timeout=timeout, sleep=sleep, do_retry=lambda e: isinstance(e, NoSuchElementException))(get)()

    def browse_shop(self):
        self.webdriver.get(f"{self.public_url}/shop")
        self.wait_for_page(title="Makerspace Webshop")
        