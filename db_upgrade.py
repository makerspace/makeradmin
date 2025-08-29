#!/usr/bin/env python3
import sys
from subprocess import DEVNULL, CalledProcessError, Popen, run
from time import sleep

from db_backup import backup_database
from db_restore import restore_database


def confirm_action(prompt: str = "Are you sure you want to continue? [y/n] ", exit_on_no: bool = True) -> bool:
    while True:
        yn = input(prompt).strip().lower()
        if yn in ("y", "yes"):
            break
        elif yn in ("n", "no"):
            if exit_on_no:
                sys.exit(0)
            else:
                return False
        else:
            print("Please answer yes or no.")
    return True


confirm_action(
    "This script is for upgrading the database engine version."
    "This will involve backing up your current database, deleting it, and then restoring it! Are you sure you want to continue? [y/n] "
)

try:
    result = run(
        ["docker", "compose", "-f", "docker-compose.yml", "ps", "-q", "db2"],
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():
        print("Error: Database container 'db2' is already running. Please stop it before proceeding.")
        sys.exit(1)
except CalledProcessError as e:
    print("Error checking database container status.")
    sys.exit(1)

print("Starting database container...")
run(["docker", "compose", "-f", "docker-compose.yml", "up", "-d", "db2"], check=True)
sleep(3)

exported_path = backup_database()
print(f"Database backup created at: {exported_path}")

run(["docker", "compose", "-f", "docker-compose.yml", "down", "db2"], check=True)

confirm_action("To continue, we must delete your database volume. Continue? [y/n] ")

run(
    ["docker", "volume", "rm", "makeradmin_dbdata"],
    check=True,
)

print("Now do the following:")
print("Update the database docker image in docker-compose.yml. Check https://hub.docker.com/_/mysql/tags")

confirm_action("Have you updated the database docker image, and want to continue restoring the db? [y/n] ")

run(["docker", "compose", "-f", "docker-compose.yml", "up", "-d", "db2"], check=True)
sleep(3)

restore_database(exported_path)

run(["docker", "compose", "-f", "docker-compose.yml", "down", "db2"], check=True)
