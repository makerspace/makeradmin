import argparse
import os
import secrets

from zoneinfo import available_timezones

parser = argparse.ArgumentParser(description="Create a default '.env' file with secrets if it doesn't exist")
parser.add_argument("--force", "-f", dest="force", action="store_true", help="overwrite existing '.env' file")
parser.add_argument("--interactive", "-i", dest="interactive", action="store_true", help="run with interactive choices")

args = parser.parse_args()

if not args.force and os.path.isfile(".env"):
    print(".env file already exists, touching")
    os.utime(".env", None)
    exit()

if args.interactive:
    while True:
        zone_str = input("What is the makerspace timezone? [Y/n]: ")

        if zone_str in available_timezones():
            makerspace_local_timezone = zone_str
            break
        else:
            print(f"Timezone {zone_str} is not in the list of available zones")
else:
    makerspace_local_timezone = "Europe/Stockholm"

config = {
    "MYSQL_DB": "makeradmin",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "makeradmin",
    "MYSQL_PASS": secrets.token_hex(16),
    "MYSQL_ROOT_PASSWORD": secrets.token_hex(16),
    # Note: This must fit into the access_tokens table in the database
    "TEST_SERVICE_TOKEN": secrets.token_hex(16),
    "MAILGUN_DOMAIN": "",
    "MAILGUN_KEY": "",
    "MAILGUN_FROM": "MakerAdmin <excited@samples.mailgun.org>",
    "MAILGUN_TO_OVERRIDE": "",
    "HOST_BACKEND": "http://localhost:8010",
    "HOST_FRONTEND": "http://localhost:8009",
    "HOST_PUBLIC": "http://localhost:8011",
    "ADMIN_EMAIL": "",
    "STRIPE_PRIVATE_KEY": os.environ.get("STRIPE_PRIVATE_KEY", ""),
    "STRIPE_PUBLIC_KEY": os.environ.get("STRIPE_PUBLIC_KEY", ""),
    "STRIPE_SIGNING_SECRET": "",
    "STRIPE_CURRENCY": "sek",
    "ACCESSY_CLIENT_ID": "",
    "ACCESSY_CLIENT_SECRET": "",
    "ACCESSY_LABACCESS_GROUP": "",
    "ACCESSY_SPECIAL_LABACCESS_GROUP": "",
    "ACCESSY_DO_MODIFY": "false",
    "CORS_ALLOWED_ORIGINS": "http://localhost:8009,http://localhost:8011,http://localhost:8080",
    "FIRSTRUN_AUTO_ADMIN_FIRSTNAME": "",
    "FIRSTRUN_AUTO_ADMIN_LASTNAME": "",
    "FIRSTRUN_AUTO_ADMIN_EMAIL": "",
    "FIRSTRUN_AUTO_ADMIN_PASSWORD": "",
    "ELKS46_API_USER": "",
    "ELKS46_API_KEY": "",
    "MAKERSPACE_LOCAL_TIMEZONE": makerspace_local_timezone,
}


with open(".env", "w") as f:
    f.write("\n".join(key + "=" + value for (key, value) in config.items()))
