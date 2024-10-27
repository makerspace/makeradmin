import argparse
import os
import secrets

parser = argparse.ArgumentParser(description="Create a default '.env' file with secrets if it doesn't exist")
parser.add_argument("--force", "-f", dest="force", action="store_true", help="overwrite existing '.env' file")
args = parser.parse_args()

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
    "PROTOCOL": "http",
    "HOST_BACKEND": "localhost:8010",
    "HOST_FRONTEND": "localhost:8009",
    "HOST_PUBLIC": "localhost:8011",
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
    "FIRSTRUN_AUTO_ADMIN_FIRSTNAME": "",
    "FIRSTRUN_AUTO_ADMIN_LASTNAME": "",
    "FIRSTRUN_AUTO_ADMIN_EMAIL": "",
    "FIRSTRUN_AUTO_ADMIN_PASSWORD": "",
    "ELKS46_API_USER": "",
    "ELKS46_API_KEY": "",
}

if not args.force and os.path.isfile(".env"):
    print(".env file already exists, touching")
    os.utime(".env", None)
else:
    with open(".env", "w") as f:
        f.write("\n".join(key + "=" + value for (key, value) in config.items()))
