import secrets
import argparse
import os

parser = argparse.ArgumentParser(description='Create a default \'.env\' file with secrets if it doesn\'t exist')
parser.add_argument('--force','-f', dest='force', action='store_true', help='overwrite existing \'.env\' file')
args = parser.parse_args()

config = {
    "COMPOSE_PROJECT_NAME": "makeradmin",
    "MYSQL_DB": "makerdata",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "makeradmin",
    "MYSQL_PASS": secrets.token_hex(16),
    "MYSQL_ROOT_PASSWORD": secrets.token_hex(16),
    # Note: This must fit into the access_tokens table in the database
    "API_BEARER": secrets.token_hex(16),
    "TICTAIL_USER": "",
    "TICTAIL_PASS": "",
    "TICTAIL_STORE": "",
    "MAILGUN_DOMAIN": "",
    "MAILGUN_KEY": "",
    "MAILGUN_FROM": "MakerAdmin <excited@samples.mailgun.org>",
    "MAILGUN_TO_OVERRIDE": "",
    "HOST_BACKEND": "http://localhost:8010",
    "HOST_FRONTEND": "http://localhost:8009",
    "STRIPE_PRIVATE_KEY": "",
    "STRIPE_PUBLIC_KEY": "",
    "STRIPE_SIGNING_SECRET": "",
    "APP_DEBUG": "false",
}

if not args.force and os.path.isfile(".env"):
    print('.env file already exists, touching')
    os.utime(".env", None)
else:
    with open(".env", "w") as f:
        f.write("\n".join(key + "=" + value for (key, value) in config.items()))
