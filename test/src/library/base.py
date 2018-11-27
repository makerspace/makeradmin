import os
from collections.abc import Mapping

import requests

from unittest import TestCase
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote import webdriver as remote
from selenium.webdriver.chrome import webdriver as chrome


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
    
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.token = get_env("API_BEARER")
        self.host = get_env("HOST_BACKEND")

    def post(self, path=None, json=None, headers=None):
        headers = headers or {"Authorization": "Bearer " + self.token}
        url = self.host + "/" + path
        return ApiResponse(requests.post(url, json=json, headers=headers), self)
        
    def put(self, path=None, json=None, headers=None):
        headers = headers or {"Authorization": "Bearer " + self.token}
        url = self.host + "/" + path
        return ApiResponse(requests.put(url, json=json, headers=headers), self)

    def delete(self, path=None, json=None, headers=None):
        headers = headers or {"Authorization": "Bearer " + self.token}
        url = self.host + "/" + path
        return ApiResponse(requests.delete(url, json=json, headers=headers), self)

    def get(self, path=None, params=None, headers=None):
        headers = headers or {"Authorization": "Bearer " + self.token}
        url = self.host + "/" + path
        return ApiResponse(requests.get(url, params=params, headers=headers), self)
