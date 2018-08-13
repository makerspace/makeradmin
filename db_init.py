from subprocess import call, check_output, STDOUT
import sys
from time import sleep
import argparse
import multiprocessing

containers = ["api-gateway", "membership", "messages", "economy", "rfid", "webshop"]

parser = argparse.ArgumentParser(description='Initialize the database and run migrations')
parser.add_argument('--project-name','-p', help='Use a different docker composer project name', default="makeradmin")
parser.add_argument('--containers','-c', nargs="*", default=containers, help='All containers to update')
args = parser.parse_args()

containers = args.containers

call(["docker-compose", "-p", args.project_name, "up", "-d", "db2"])

print("Waiting for database", end="")
inner_bash = 'while ! mysql -uroot --password="${MYSQL_ROOT_PASSWORD}" -e "" &> /dev/null; do printf "." && sleep 1; done'
call(["docker-compose", "-p", args.project_name, "exec", "db2", "bash", "-c", inner_bash])

# Make sure all docker containers are created (but not necessarily started)
call(["docker-compose", "-p", args.project_name, "up", "--no-start"])

print(" done")

sleep(1)


def init_container(container):
    # This is how the names appear to be formatted.
    # If necessary 'docker-compose ps -q {container}' can be used, but that is a lot slower
    container_name = f"{args.project_name}_{container}_1"
    print(f"Initializing database for {container}...")

    # Get environment variables for the docker container
    env = dict(
        row.split("=") for row in
        check_output([
            "docker", "inspect", "-f", "{{range $index, $value := .Config.Env}}{{println $value}}{{end}}", container_name
        ]).decode('utf-8').strip().split("\n")
    )
    mysql_db, mysql_user, mysql_pass = env["MYSQL_DB"], env["MYSQL_USER"], env["MYSQL_PASS"]

    # Note "{{x}}" escapes to "{x}"
    inner_bash3 = f"""
    mysql -uroot --password="${{MYSQL_ROOT_PASSWORD}}" -e "
    CREATE USER IF NOT EXISTS \`{mysql_user}\`@'%' IDENTIFIED BY '{mysql_pass}';
    CREATE DATABASE IF NOT EXISTS \`{mysql_db}\`;
    GRANT ALL ON \`{mysql_db}\`.* TO \`{mysql_user}\`@'%';
    FLUSH PRIVILEGES;"
    mysql -uroot --password="${{MYSQL_ROOT_PASSWORD}}" -e "FLUSH PRIVILEGES;"
    """
    o1 = check_output(["docker-compose", "-p", args.project_name, "exec", "db2", "bash", "-c", inner_bash3], stderr=STDOUT)
    o1 = o1.decode('utf-8').strip().replace('\r', '')
    o1 = o1.replace("mysql: [Warning] Using a password on the command line interface can be insecure.", "").strip()
    if o1 != "":
        print(o1)

    migrate = f"""
        if [ -f /var/www/html/artisan ]; then php /var/www/html/artisan --force migrate;
        elif [ -f /var/www/service/migrate.py ]; then echo 'Migrating using Python'; python3 /var/www/service/migrate.py;
        else echo \"No migration script found. Skipping migration for {container}\";
        fi
    """
    call(["docker-compose", "-p", args.project_name, "run", "--rm", "--no-deps", container, "bash", "-c", migrate])

for container in containers:
    init_container(container)
