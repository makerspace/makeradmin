import os


env = None


# TODO Use rocky / python-dotenv.
def get_env(name):
    """ Read variable from os environment, if not exists try to read from .env-file. Inside the test container the
    .env-file is not available all variables should be provided through the docker-compose.test.yml file. """
    
    global env
    if env is None:
        try:
            filename = os.path.abspath(f"{os.path.dirname(__file__)}/../../../../.env")
            with open(filename) as f:
                env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}
        except OSError:
            env = {}
    
    if name in os.environ:
        return os.environ[name]
    
    return env[name]


HOST_FRONTEND = get_env("HOST_FRONTEND")

HOST_PUBLIC = get_env("HOST_PUBLIC")

HOST_BACKEND = get_env("HOST_BACKEND")

STRIPE_PUBLIC_KEY = get_env("STRIPE_PUBLIC_KEY")

WEBDRIVER_TYPE = os.environ.get('WEBDRIVER_TYPE', 'CHROME')

KEEP_BROWSER = os.environ.get('KEEP_BROWSER')

SELENIUM_BASE_TIMEOUT = float(os.environ.get('SELENIUM_BASE_TIMEOUT', '4.0'))

SLEEP = 0.2

SELENIUM_SCREENSHOT_DIR = os.environ.get('SELENIUM_SCREENSHOT_DIR',
                                         os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                      f"../../../.test/selenium-screenshots")))

API_BEARER = get_env("API_BEARER")
