import argparse
import os
import secrets

parser = argparse.ArgumentParser(description="Create a default '.env' file with secrets if it doesn't exist")
parser.add_argument("--force", "-f", dest="force", action="store_true", help="overwrite existing '.env' file")
parser.add_argument("--interactive", "-i", dest="interactive", action="store_true", help="run with interactive choices")

args = parser.parse_args()

if not args.force and os.path.isfile(".env"):
    print(".env file already exists, touching")
    os.utime(".env", None)
    exit(0)

if args.interactive:
    while True:
        zone_str = input("Enter the makerspace timezone [Europe/Stockholm]: ") or "Europe/Stockholm"
        if zone_str:
            makerspace_local_timezone = zone_str
            break
        else:
            print(f"Timezone '{zone_str}' is not valid.")
            print("Please enter a valid timezone (e.g., 'Europe/Stockholm').")

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
    "PROTOCOL": "http",
    "HOST_BACKEND": "localhost:8010",
    "HOST_FRONTEND": "localhost:8009",
    "HOST_PUBLIC": "localhost:8011",
    "ADMIN_EMAIL": "",
    "STRIPE_PRIVATE_KEY": os.environ.get("STRIPE_PRIVATE_KEY", ""),
    "STRIPE_PUBLIC_KEY": os.environ.get("STRIPE_PUBLIC_KEY", ""),
    "STRIPE_SIGNING_SECRET": "",
    "STRIPE_CURRENCY": "sek",
    "ACCESSY_URL": "https://api.accessy.se",
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
    "MAKERSPACE_LOCAL_TIMEZONE": makerspace_local_timezone,
}

whitelist = ["COMPOSE_PROJECT_NAME"]

YELLOW = "\u001b[33m"
GREEN = "\u001b[32m"
RED = "\u001b[31m"
BLUE = "\u001b[34m"
RESET = "\u001b[0m"

if not args.force and os.path.isfile(".env"):
    print(".env file already exists, touching")

    with open(".env", "r") as f:
        data = f.read()

    items = [tuple(l.split("=")) if "=" in l else ("", l.strip()) for l in data.strip().splitlines()]
    for key, value in items:
        # If the key=value pair is not:
        # - a known key
        # - or an empty line
        # - or commented out and the default value is either empty or identical to the commented out value
        # then warn about an unknown key
        if (
            key != ""
            and key not in whitelist
            and key not in config
            and not (key.replace("#", "") in config and config[key.replace("#", "")] in ["", value])
        ):
            print(
                f"{YELLOW}Unknown key {key}='{value}' in your .env file. You should be able to safely remove it.{RESET}"
            )

    for key, value in config.items():
        if not any(k == key or k == f"#{key}" for (k, v) in items):
            print(f"{GREEN}Adding new key {key}='{value}' to your .env file.{RESET}")
            items.append((key, value))

    with open(".env", "w") as f:
        f.write("\n".join(f"{key}={value}" if key != "" else value for (key, value) in items))
else:
    with open(".env", "w") as f:
        f.write("\n".join(key + "=" + value for (key, value) in config.items()))
