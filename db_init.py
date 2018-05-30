from subprocess import call, check_output, STDOUT
import sys
from time import sleep

containers = ["api-gateway", "membership", "messages", "sales", "economy", "rfid", "webshop"]

if len(sys.argv) > 1:
    containers = sys.argv[1:]

call("docker-compose up -d db2", shell=True)
db_hash = check_output("docker-compose ps -q db2", shell=True).decode('utf-8')
assert(db_hash != "")

print("Waiting for database", end="")
inner_bash = 'while ! mysql -uroot --password="${MYSQL_ROOT_PASSWORD}" -e "" &> /dev/null; do printf "." && sleep 1; done'
call(["docker-compose", "exec", "db2", "bash", "-c", inner_bash])

print(" done")

sleep(1)
for container in containers:
    print(f"Initializing database for {container}...")
    inner_bash2 = 'printf "%s|%s|%s" "${MYSQL_DB}" "${MYSQL_USER}" "${MYSQL_PASS}"'
    mysql_db, mysql_user, mysql_pass = check_output(["docker-compose", "run", "--rm", "--no-deps", container, "bash", "-c", inner_bash2]).decode('utf-8').split("|")
    # Note "{{x}}" escapes to "{x}"
    inner_bash3 = f"""mysql -uroot --password="${{MYSQL_ROOT_PASSWORD}}" -e "
    CREATE USER IF NOT EXISTS \`{mysql_user}\`@'%' IDENTIFIED BY '{mysql_pass}';
    CREATE DATABASE IF NOT EXISTS \`{mysql_db}\`;
    GRANT ALL ON \`{mysql_db}\`.* TO \`{mysql_user}\`@'%';
    FLUSH PRIVILEGES;"
  """
    o1 = check_output(["docker-compose", "exec", "db2", "bash", "-c", inner_bash3], stderr=STDOUT)
    if o1 != b'mysql: [Warning] Using a password on the command line interface can be insecure.\r\n':
        print(o1.decode('utf-8'))

    o2 = check_output(["docker-compose", "exec", "db2", "bash", "-c", 'mysql -uroot --password="${MYSQL_ROOT_PASSWORD}" -e "FLUSH PRIVILEGES;"'], stderr=STDOUT)
    if o2 != b'mysql: [Warning] Using a password on the command line interface can be insecure.\r\n':
        print(o2.decode('utf-8'))

    migrate_artisan = f"if [ -f /var/www/html/artisan ]; then php /var/www/html/artisan --force migrate; else echo \"artisan not found, skipping migration for {container}\"; fi"
    call(["docker-compose", "run", "--rm", "--no-deps", container, "bash", "-c", migrate_artisan])
    migrate_python = f"if [ -f /var/www/service/migrate.py ]; then echo 'Migrating using Python'; python3 /var/www/service/migrate.py; fi"
    call(["docker-compose", "run", "--rm", "--no-deps", container, "bash", "-c", migrate_python])
