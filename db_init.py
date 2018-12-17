#!python3
from subprocess import call, check_output, STDOUT
from time import sleep
import argparse


containers = ["api-gateway", "membership", "messages", "backend"]

parser = argparse.ArgumentParser(description='Initialize the database and run migrations')
parser.add_argument('--project-name', '-p', help='Use a different docker composer project name', default=None)
parser.add_argument('--containers', '-c', nargs="*", default=containers, help='All containers to update')
args = parser.parse_args()

project_name_args = ["-p", args.project_name] if args.project_name is not None else []
containers = args.containers

call(["docker-compose", *project_name_args, "up", "-d", "db2"])

print("Waiting for database", end="")
cmd = 'while ! mysql -uroot --password="${MYSQL_ROOT_PASSWORD}" -e "" &> /dev/null; do printf "." && sleep 1; done'
call(["docker-compose", *project_name_args, "exec", "db2", "bash", "-c", cmd])
print(" done")

# Make sure all docker containers are created (but not necessarily started)
# This is important when running unit tests.
#call(["docker-compose", *project_name_args, "up", "--no-start"])


sleep(1)


with open('.env') as f:
    env = {s[0]: (s[1] if len(s) > 1 else "") for s in (s.split("=") for s in f.read().split('\n'))}


for container in containers:
    # This call takes quite a long time (0.7 seconds on my machine)
    # which adds up to a lot when running tests, therefore a shortcut is used above if possible.
    print(f"Initializing database for {container}...")

    mysql_db, mysql_user, mysql_pass = env["MYSQL_DB"], env["MYSQL_USER"], env["MYSQL_PASS"]

    cmd = f"""
    mysql -uroot -p"${{MYSQL_ROOT_PASSWORD}}" -e "
    CREATE USER IF NOT EXISTS \`{mysql_user}\`@'%' IDENTIFIED BY '{mysql_pass}';
    CREATE DATABASE IF NOT EXISTS \`makeradmin\`;
    GRANT ALL ON \`makeradmin\`.* TO \`{mysql_user}\`@'%';
    FLUSH PRIVILEGES;"
    """
    o1 = check_output(["docker-compose", *project_name_args, "exec", "db2", "bash", "-c", cmd], stderr=STDOUT)
    o1 = o1.decode('utf-8').strip().replace('\r', '')
    o1 = o1.replace("mysql: [Warning] Using a password on the command line interface can be insecure.", "").strip()
    if o1 != "":
        print(o1)

    migrate = f"""
        if [ -f /var/www/html/artisan ]; then php /var/www/html/artisan --force migrate;
        elif [ -f /work/src/migrate.py ]; then echo 'Migrating using Python'; python3 /work/src/migrate.py;
        else echo \"No migration script found. Skipping migration for {container}\";
        fi
    """
    call(["docker-compose", *project_name_args, "run", "--rm", "--no-deps", container, "bash", "-c", migrate])
