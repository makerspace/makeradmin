import os
import sys
import time
from functools import wraps
from logging import getLogger
from typing import Optional
from unittest import SkipTest, skipIf
from sqlalchemy import create_engine

import stripe
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote import webdriver as remote
from selenium.webdriver.chrome import webdriver as chrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

from service.config import get_mysql_config
from service.db import create_mysql_engine, db_session_factory, db_session
from shop.stripe_constants import EventType, set_stripe_key
from test_aid.api import ApiFactory, ApiResponse
from test_aid.db import DbFactory
from test_aid.obj import DEFAULT_PASSWORD
from test_aid.systest_config import HOST_FRONTEND, HOST_PUBLIC, HOST_BACKEND, \
    SELENIUM_BASE_TIMEOUT, SLEEP, WEBDRIVER_TYPE, TEST_SERVICE_TOKEN, SELENIUM_SCREENSHOT_DIR, KEEP_BROWSER, \
    STRIPE_PUBLIC_KEY
from test_aid.test_base import TestBase, ShopTestMixin

VALID_NON_3DS_CARD_NO = "378282246310005"
VALID_3DS_CARD_NO = "4242424242424242"
EXPIRED_3DS_CARD_NO = "4000000000000069"
DECLINE_AFTER_ATTACHING_CARD = "4000000000000341"
EXPIRED_CVC_ZIP = "4242424242424"

logger = getLogger('makeradmin')


class SystestBase(TestBase):
    """ Base class for systest with config available. """
    db: DbFactory
    admin_url: str
    public_url: str
    api_url: str

    @classmethod
    def setUpClass(self) -> None:
        super().setUpClass()

        # Use the public key for these tests. TODO: Why not the private one?
        set_stripe_key(False)
        
        # Make sure sessions is removed so it is not using another engine in this thread.
        db_session.remove()
        
        if "TEST_IS_INSIDE_DOCKER" not in os.environ:
            # This test requires a connection to the mysql database instead of just an in-memory db.
            # Therefore we only run this test when we are inside docker.
            raise SkipTest("Not running inside docker")

        create_mysql_engine(**get_mysql_config(), isolation_level="READ_COMMITTED")
        
        self.db = DbFactory(self, self.obj)
        self.admin_url = HOST_FRONTEND
        self.public_url = HOST_PUBLIC
        self.api_url = HOST_BACKEND
        
    def tearDown(self) -> None:
        super().tearDown()
        db_session.close()

    
class ApiTest(SystestBase):
    """ Base class for tests that accesses the api. """
    
    api: Optional[ApiFactory] = None
    
    @classmethod
    def setUpClass(self) -> None:
        super().setUpClass()
        self.api = ApiFactory(obj_factory=self.obj, base_url=self.api_url, api_token=TEST_SERVICE_TOKEN)

    def request(self, *args, **kwargs) -> ApiResponse:
        assert self.api is not None
        return self.api.request(*args, **kwargs)

    def post(self, *args, **kwargs) -> ApiResponse:
        assert self.api is not None
        return self.api.post(*args, **kwargs)

    def put(self, *args, **kwargs) -> ApiResponse:
        assert self.api is not None
        return self.api.put(*args, **kwargs)

    def delete(self, *args, **kwargs) -> ApiResponse:
        assert self.api is not None
        return self.api.delete(*args, **kwargs)

    def get(self, *args, **kwargs) -> ApiResponse:
        assert self.api is not None
        return self.api.get(*args, **kwargs)


def retry(timeout=SELENIUM_BASE_TIMEOUT, sleep=SLEEP, retry_exception=None, retry_result=None):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrap(*args, **kwargs):
            start = time.perf_counter()
            while True:
                try:
                    result = wrapped(*args, **kwargs)
                    elapsed = time.perf_counter() - start
                    if not retry_result or elapsed > timeout or not retry_result(result):
                        return result
                except Exception as e:
                    elapsed = time.perf_counter() - start
                    if elapsed > timeout or not retry_exception(e):
                        raise
                    print(f"{wrapped.__qualname__} failed with the following error after {elapsed:02f}s:"
                          f" {e.__class__.__name__} {str(e)}",
                          file=sys.stderr)
                time.sleep(sleep)
        return wrap
    return decorator
    

def create_webdriver():
    if WEBDRIVER_TYPE == 'CHROME':
        return chrome.WebDriver()
    
    if WEBDRIVER_TYPE == 'REMOTE_CHROME':
        return remote.WebDriver(command_executor='http://selenium:4444/wd/hub',
                                options=webdriver.ChromeOptions())
    
    raise Exception(f"bad webdriver type {WEBDRIVER_TYPE}")


class SeleniumTest(ApiTest):
    """ Base class for selenium tests. """
    
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
        if not KEEP_BROWSER and getattr(self, "webdriver"):
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
                return self.webdriver.find_element(By.ID, id)
        elif name:
            def get():
                return self.webdriver.find_element(By.NAME, name)
        elif tag:
            def get():
                return self.webdriver.find_element(By.TAG_NAME, tag)
        elif css:
            def get():
                return self.webdriver.find_element(by=By.CSS_SELECTOR, value=css)
        elif xpath:
            def get():
                return self.webdriver.find_element(By.XPATH, xpath)
        else:
            raise Exception("missing parameter")
        
        return retry(timeout=timeout, sleep=sleep, retry_exception=lambda e: isinstance(e, NoSuchElementException))(get)()

    def wait_for_elements(self, id=None, name=None, tag=None, css=None, xpath=None, expected_count=None,
                          timeout=SELENIUM_BASE_TIMEOUT, sleep=SLEEP):
        if id:
            def get():
                return self.webdriver.find_elements(By.ID, id)
        elif name:
            def get():
                return self.webdriver.find_elements(By.NAME, name)
        elif tag:
            def get():
                return self.webdriver.find_elements(By.TAG_NAME, tag)
        elif css:
            def get():
                return self.webdriver.find_elements(By.CSS_SELECTOR, css)
        elif xpath:
            def get():
                return self.webdriver.find_elements(By.XPATH, xpath)
        else:
            raise Exception("missing parameter")
        
        return retry(
            timeout=timeout, sleep=sleep,
            retry_exception=lambda e: isinstance(e, NoSuchElementException),
            retry_result=lambda r: len(r) != expected_count
        )(get)()

    def browse_member_page(self):
        self.webdriver.get(f"{self.public_url}/member")
        self.wait_for_page(title="Medlemssidor - Stockholm Makerspace Webshop")
        
    def browse_shop(self):
        self.webdriver.get(f"{self.public_url}/shop")
        self.wait_for_page(title="Stockholm Makerspace Webshop")

    def browse_cart_page(self):
        self.webdriver.get(f"{self.public_url}/shop/cart")
        self.wait_for_page(title="Stockholm Makerspace Webshop")
        
        
class ApiShopTestMixin(ShopTestMixin):
    
    @skipIf(not stripe.api_key, "webshop tests require stripe api key in .env file")
    def setUp(self):
        super().setUp()
        self.member = self.api.create_member(unhashed_password=DEFAULT_PASSWORD)
        self.member_id = self.member['member_id']
        self.test_start_timestamp = str(int(time.time()))
        self.token = self.factory.login_member()

    def trigger_stripe_source_event(self, source_id, expected_event_count=1):
        """ Make server fetch events and filter it on source and type, do this until one event was processed. """
        
        for i in range(10):
            event_count = self.post(
                f"/webshop/process_stripe_events",
                dict(
                    start=self.test_start_timestamp,
                    type=f"{EventType.SOURCE}*",
                    source_id=source_id,
                )
            ).expect(200).data
            
            if event_count >= expected_event_count:
                return
                
            time.sleep(1)
            
        raise AssertionError(f"failed to get source events for {source_id}")
