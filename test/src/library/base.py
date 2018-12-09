import os
from collections.abc import Mapping
from datetime import datetime, timedelta

import requests

from unittest import TestCase

import stripe
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote import webdriver as remote
from selenium.webdriver.chrome import webdriver as chrome

from library.factory import MemberFactory, GroupFactory, CategoryFactory, ProductFactory

webdriver_type = os.environ.get('WEBDRIVER_TYPE', 'CHROME')
keep_browser = os.environ.get('KEEP_BROWSER')
test_mode = os.environ.get('TEST_MODE', 'DEV')
try:
    with open(f"{os.path.dirname(__file__)}/../../../.env") as f:
        env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}
except OSError:
    env = {}


def create_webdriver():
    if webdriver_type == 'CHROME':
        return chrome.WebDriver()
    
    if webdriver_type == 'REMOTE_CHROME':
        return remote.WebDriver(command_executor='http://selenium:4444/wd/hub',
                                desired_capabilities=DesiredCapabilities.CHROME)
    
    raise Exception(f"bad webdriver type {webdriver_type}")


def get_env(name):
    """ Read variable from os environment, if not exists try to read from .env-file. """
    if name in os.environ:
        return os.environ[name]
    
    return env[name]


class TestCaseBase(TestCase):
    
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

        self.now = datetime.now()
        self.today = self.now.date()
        
    def date(self, days=0):
        return self.today + timedelta(days=days)
        

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


def get_path(obj, path):
    """ Return value from path in obj or None. """
    for seg in path.split('__'):
        try:
            obj = obj[seg]
        except (AttributeError, TypeError, KeyError):
            return None
    return obj
    
    
def merge_paths(**kwargs):
    """
    Return dict of path => value with paths on the form segment__segment__segment built by merging kwargs where each
    kwarg can be a full path, a partial path ending in a dict of paths or a dict. If there are conflicts the last
    value will be used.
    
    Examples:
        megrge_paths(a__path=1, a={'b': 2}, {'c': 3}) => {'a__path': 1, 'a__b': 2, 'c': 3}
        megrge_paths(a__path=1, a={'path': 2}) => {'a__path': 2}
    """
    res = {}
    
    def flatten(key, obj):
        if isinstance(obj, Mapping):
            for k, o in obj.items():
                flatten(f"{key}__{k}", o)
        else:
            res[key] = obj
    
    for key, obj in kwargs.items():
        flatten(key, obj)
    
    return res
    
    
class ApiResponse:
    
    def __init__(self, response, test):
        self.response = response
        self.test = test
        
    def expect(self, code=None, **kwargs):
        if code is not None:
            self.test.assertEqual(code, self.response.status_code,
                                  msg=f"bad status, url: {self.response.url}, content: {self.response.text}")
        
        data = self.response.json()
        for path, expected_value in merge_paths(**kwargs).items():
            value = get_path(data, path)
            self.test.assertEqual(expected_value, value,
                                  msg=f"bad value at path '{path}', url: {self.response.url}, content: {self.response.text}")
        
        return self
    
    @property
    def data(self):
        return self.get('data')
    
    def get(self, *paths):
        data = self.response.json()
        result = [get_path(data, path) for path in paths]
        if len(result) == 1:
            return result[0]
        return result
    
    def print(self):
        print(self.response.text)
        return self
    

class ApiTest(TestCaseBase):

    ADD_MEMBERSHIP_DAYS = 1
    ADD_LABACCESS_DAYS = 2
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.api_token = get_env("API_BEARER")
        self.host = get_env("HOST_BACKEND")
        stripe.api_key = get_env("STRIPE_PUBLIC_KEY")

    def request(self, method, path, **kwargs):
        token = kwargs.pop('token', self.api_token)
        headers = kwargs.pop('headers', {"Authorization": "Bearer " + token})
        url = self.host + "/" + path
        return ApiResponse(requests.request(method, url=url, headers=headers, **kwargs), self)

    def post(self, path, json=None, **kwargs):
        return self.request("post", path, json=json, **kwargs)

    def put(self, path, json=None, **kwargs):
        return self.request("put", path, json=json, **kwargs)

    def delete(self, path, json=None, **kwargs):
        return self.request("delete", path, json=json, **kwargs)
        
    def get(self, path, params=None, **kwargs):
        return self.request("get", path, params=params, **kwargs)

    def api_create_member(self, **kwargs):
        return self.post("membership/member", json=MemberFactory(**kwargs)).expect(code=201, status='created').data

    def api_create_group(self, **kwargs):
        return self.post("membership/group", json=GroupFactory(**kwargs)).expect(code=201, status='created').data

    def api_create_category(self, **kwargs):
        return self.post("webshop/category", json=CategoryFactory(**kwargs)).expect(code=200, status='created').data
        
    def api_create_product(self, **kwargs):
        return self.post("webshop/product", json=ProductFactory(**kwargs)).expect(code=200, status='created').data

    def api_create_product_action(self, **kwargs):
        action = {
            "product_id": 0,
            "action_id": self.ADD_MEMBERSHIP_DAYS,
            "value": 365
        }
        action.update(**kwargs)
        return self.post(f"/webshop/product_action", action).expect(code=200, status='created').data
