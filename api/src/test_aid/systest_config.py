import os
from logging import INFO

from dotenv import dotenv_values, find_dotenv
from rocky.config import Config, Dict, Env

env = Env()


dot_env_filename = find_dotenv()
dot_env = Dict(src=dotenv_values(dot_env_filename), name=dot_env_filename)

config = Config(env, dot_env, log_level=INFO)


HOST_FRONTEND = config.get("HOST_FRONTEND")

HOST_PUBLIC = config.get("HOST_PUBLIC")

HOST_BACKEND = config.get("HOST_BACKEND")

STRIPE_PUBLIC_KEY = config.get("STRIPE_PUBLIC_KEY")

STRIPE_PRIVATE_KEY = config.get("STRIPE_PRIVATE_KEY")

WEBDRIVER_TYPE = config.get("WEBDRIVER_TYPE", default="CHROME")

KEEP_BROWSER = config.get("KEEP_BROWSER")

SELENIUM_BASE_TIMEOUT = float(config.get("SELENIUM_BASE_TIMEOUT", default="4.0"))

SLEEP = 0.2

SELENIUM_SCREENSHOT_DIR = config.get(
    "SELENIUM_SCREENSHOT_DIR",
    default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.test/selenium-screenshots")),
)

TEST_SERVICE_TOKEN = config.get("TEST_SERVICE_TOKEN")
