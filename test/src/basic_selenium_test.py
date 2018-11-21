import os
import sys
from unittest import TestCase

from selenium.webdriver.chrome import webdriver


class Test(TestCase):
    
    def test_noop(self):
        print(os.environ['PATH'], file=sys.stderr)
        options = webdriver.Options()
        options.add_argument("--lang=en")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("prefs", {'intl.accept_languages': 'en'})
        browser = webdriver.WebDriver(options=options)
        
        browser.get("http://admin/")
        browser.save_screenshot("/tmp/fil.png")
        
        browser.close()
