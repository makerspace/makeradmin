import sys
import os
import argparse
from subprocess import call, STDOUT, check_output
import create_user

YELLOW = "\u001b[33m"
GREEN = "\u001b[32m"
RESET = "\u001b[0m"

parser = argparse.ArgumentParser(
    description='Initialize the database and run migrations')
parser.add_argument('--project-name', '-p',
                    help='Use a different docker composer project name', default=None)
args = parser.parse_args()

project_name_args = [
    "-p", args.project_name] if args.project_name is not None else []


def assert_call(args, **kwargs):
    exitcode = call(args, **kwargs)
    if exitcode != 0:
        print("Running", args, "failed with exit code", exitcode)
        exit(exitcode)


print(YELLOW + "Initializing the database" + RESET)
assert_call(["python3", "db_init.py"])

print(YELLOW + "Starting makeradmin" + RESET)
assert_call(["docker-compose", *project_name_args, "up", "-d"])

print(YELLOW + "Waiting for database" + RESET)
cmd = 'while ! mysql -uroot --password="${MYSQL_ROOT_PASSWORD}" -e "" &> /dev/null; do printf "." && sleep 1; done'
assert_call(["docker-compose", *project_name_args, "exec", "db2", "bash", "-c", cmd])

print(YELLOW + "Waiting for makeradmin to come online", end="")
assert_call(["docker-compose", *project_name_args, "exec", "membership", "bash", "-c", "/usr/local/myscripts/wait-for api-gateway:80"])
print(".", end="")
assert_call(["docker-compose", *project_name_args, "exec", "membership", "bash", "-c", "/usr/local/myscripts/wait-for backend:80"])
print(".", end="")
assert_call(["docker-compose", *project_name_args, "exec", "membership", "bash", "-c", "/usr/local/myscripts/wait-for membership:80"])
print(".", end="")
assert_call(["docker-compose", *project_name_args, "exec", "membership", "bash", "-c", "/usr/local/myscripts/wait-for admin:80"])
print(RESET)

print(YELLOW + "Adding all admin permissions" + RESET)

# Note: 'ignore' necesary to be able to run the script multiple times
cmd = 'mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" -e "use makeradmin;' \
    'insert ignore into membership_group_permissions (group_id, permission_id) select 1, permission_id from membership_permissions where permission != \'service\';' \
    'update access_tokens set permissions = null where user_id > 0;"'
sql_output = check_output(["docker-compose", *project_name_args, "exec", "db2", "bash", "-c", cmd], stderr=STDOUT)
sql_output = sql_output.decode('utf-8').strip().replace('\r', '')
sql_output = sql_output.replace(
    "mysql: [Warning] Using a password on the command line interface can be insecure.", "").strip()
if sql_output != "":
    print(RED + sql_output + RESET)
    exit(1)

while True:
    s = input(
        "Do you want to create a new admin user? (you can later use the create_user.py script to create users)\n [Y/n]: ").lower()
    if s in {"", "y", "yes"}:
        print("Creating default user:")
        firstname = input("First name: ")
        lastname = input("Last name: ")
        email = input("Email: ")
        password = input("Password: ")

        create_user.create_user(firstname, lastname, email, "admin", password)
        break
    elif s in {"n", "no"}:
        break

with open('.env') as f:
    env = {s[0]: (s[1] if len(s) > 1 else "")
           for s in (s.split("=") for s in f.read().split('\n'))}


print(f"{GREEN}All done, makeradmin is running, you can access it by going to {env['HOST_FRONTEND'] if 'HOST_FRONTEND' in env else '[.env file not configured]'}{RESET}")
