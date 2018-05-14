import secrets
import argparse
import os

config = {
    "MYSQL_DB": "makerdata",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "testuser",
    "MYSQL_PASS": secrets.token_hex(16),
    "MYSQL_ROOT_PASSWORD": secrets.token_hex(16),
    # Note: This must fit into the access_tokens table in the database
    "API_BEARER": secrets.token_hex(16),
    "TICTAIL_USER": "",
    "TICTAIL_PASS": "",
    "TICTAIL_STORE": "",
    "MAILGUN_DOMAIN": "",
    "MAILGUN_KEY": "",
    "MAILGUN_FROM": "Excited User <excited@samples.mailgun.org>",
    "MAILGUN_TO_OVERRIDE": "",
    "HOST_BACKEND": "localhost:8010",
    "HOST_FRONTEND": "localhost:8009",
}

parser = argparse.ArgumentParser(description='Create a default \'.env\' file with secrets if it doesn\'t exist')
parser.add_argument('--force','-f', dest='force', action='store_true', help='overwrite existing \'.env\' file')
args = parser.parse_args()

if not args.force and os.path.isfile(".env"):
    print('.env file already exists, touching')
    os.utime(".env", None)
else:
    with open(".env", "w") as f:
        f.write("\n".join(key + "=" + value for (key, value) in config.items()))
