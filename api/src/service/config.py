from logging import DEBUG, INFO, NOTSET
from typing import Any

from dotenv import dotenv_values, find_dotenv
from rocky.config import Config, Dict, Env
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from service.logging import logger

default = Dict(
    name="default",
    src=dict(
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
        MAKERSPACE_LOCAL_TIMEZONE="Europe/Stockholm",
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

dot_env_filename = find_dotenv()

sources = [("env", env)]
if dot_env_filename:
    dotenv = dotenv_values(dot_env_filename)
    dotenv["name"] = dot_env_filename
    sources.append((".env file at " + dot_env_filename, dotenv))

logger.info("Config sources: " + ", ".join(x[0] for x in sources))
config = Config(*[x[1] for x in sources], default, log_level=NOTSET)


def get_mysql_config() -> dict[str, str | int]:
    host = config.get("MYSQL_HOST")
    port = int(config.get("MYSQL_PORT"))
    db = config.get("MYSQL_DB")
    user = config.get("MYSQL_USER")
    pwd = config.get("MYSQL_PASS", log_value=False)
    if not pwd:
        raise NameError("config MYSQL_PASS is required")

    return dict(host=host, port=port, db=db, user=user, pwd=pwd)


def get_public_url(path: str) -> str:
    """Get public site url."""
    host = config.get("HOST_PUBLIC")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "http://" + host
    return f"{host}{path}"


def get_46elks_auth() -> tuple[str, str] | None:
    usr = config.get("ELKS46_API_USER")
    pwd = config.get("ELKS46_API_KEY", log_value=False)
    if not usr and not pwd:
        return None
    return (usr, pwd)


def get_admin_url(path: str) -> str:
    """Get public site url."""
    host = config.get("HOST_FRONTEND")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "http://" + host
    return f"{host}{path}"


def get_makerspace_local_timezone() -> ZoneInfo:
    zone_str = config.get("MAKERSPACE_LOCAL_TIMEZONE")
    if zone_str is None:
        raise NameError("Variable MAKERSPACE_LOCAL_TIMEZONE not set in .env")

    try:
        zone = ZoneInfo(zone_str)
    except ZoneInfoNotFoundError as e:
        raise NameError(f"Variable MAKERSPACE_LOCAL_TIMEZONE not set correctly in .env, failed due to {e}")
    return zone


def debug_mode() -> bool:
    return config.get("DEV_RUN") == "true"
