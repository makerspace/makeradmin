from logging import INFO

from dotenv import dotenv_values, find_dotenv
from rocky.config import Config, Dict, Env

from service.logging import logger


class DotEnvFile(Dict):
    """Config reader to read from docker .env file."""

    def __init__(self, name=None, **kwargs):
        filename = find_dotenv()
        if not filename:
            logger.info("could not find .env file, skipping")
            env: Dict[str, str] = {}
        else:
            logger.info(f"loading .env file from {filename}")
            env = dotenv_values()

        super().__init__(env, name=name or filename, **kwargs)


default = Dict(
    name="default",
    src=dict(
        ASDF="asdf2",
        MYSQL_HOST="localhost",
        MYSQL_PORT=3306,
        MYSQL_USER="makeradmin",
        MYSQL_DB="makeradmin",
        MAILGUN_KEY="",
        MAILGUN_DOMAIN="",
        MAILGUN_FROM="",
        MAILGUN_TO_OVERRIDE="",  # Send to this email address instead of the actual to, useful when developing.
        ELKS46_API_USER="",
        ELKS46_API_KEY="",
        HOST_PUBLIC="",
        STRIPE_PRIVATE_KEY=None,
        STRIPE_SIGNING_SECRET=None,
        STRIPE_CURRENCY=None,
        APP_DEBUG=None,
        CORS_ALLOWED_ORIGINS="https://medlem.makerspace.se,https://stockholm.makeradmin.se,https://medlem.dev.makerspace.se"
        ",http://localhost:8009,http://localhost:8011,http://localhost:8080",
        ACCESSY_URL="https://api.accessy.se",
        ACCESSY_CLIENT_ID=None,
        ACCESSY_CLIENT_SECRET=None,
        ACCESSY_LABACCESS_GROUP=None,
        ACCESSY_SPECIAL_LABACCESS=None,
        ACCESSY_DO_MODIFY="false",  # Do perform modify operations to Accessy, default is to log only, useful when developing.
    ),
)
env = Env()
dot_env = DotEnvFile()

config = Config(env, dot_env, default, log_level=INFO)


def get_mysql_config():
    host = config.get("MYSQL_HOST")
    port = int(config.get("MYSQL_PORT"))
    db = config.get("MYSQL_DB")
    user = config.get("MYSQL_USER")
    pwd = config.get("MYSQL_PASS", log_value=False)
    if not pwd:
        raise Exception("config MYSQL_PASS is required")

    return dict(host=host, port=port, db=db, user=user, pwd=pwd)


def get_public_url(path):
    """Get public site url."""
    host = config.get("HOST_PUBLIC")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "http://" + host
    return f"{host}{path}"


def get_46elks_auth():
    usr = config.get("ELKS46_API_USER")
    pwd = config.get("ELKS46_API_KEY", log_value=False)
    if not usr and not pwd:
        return None
    return (usr, pwd)


def get_admin_url(path):
    """Get public site url."""
    host = config.get("HOST_FRONTEND")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "http://" + host
    return f"{host}{path}"


def debug_mode() -> bool:
    return config.get("DEV_RUN") == "true"
