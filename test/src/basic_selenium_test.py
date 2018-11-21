import os
import sys
from time import sleep
from unittest import TestCase

from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.remote import webdriver as remote
from selenium.webdriver.chrome import webdriver as chrome


class Test(TestCase):
    
    def test_noop(self):
        webdriver_type = os.environ.get('WEBDRIVER_TYPE', 'CHROME')
        if webdriver_type == 'CHROME':
            options = chrome.Options()
            options.add_argument("--lang=en")
            options.add_experimental_option("prefs", {'intl.accept_languages': 'en'})
            browser = chrome.WebDriver(options=options)
        elif webdriver_type == 'REMOTE_CHROME':
            browser = remote.WebDriver(command_executor='http://selenium:4444/wd/hub',
                                       desired_capabilities=DesiredCapabilities.CHROME)
            
        else:
            raise Exception(f"bad webdriver type {webdriver_type}")

        browser.get("http://admin/")
        browser.save_screenshot("/tmp/fil.png")
        
        browser.close()
