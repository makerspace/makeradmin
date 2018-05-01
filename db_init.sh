#!/bin/bash
set -e
CONTAINERS=( api-gateway membership messages sales economy rfid )
DB_RUNNING=`docker-compose ps -q db2`
[ -z "$DB_RUNNING" ] && docker-compose up -d db2
printf "Waiting for database "
docker-compose exec db2 bash -c "while ! mysql -uroot --password=\"\${MYSQL_ROOT_PASSWORD}\" -e '' &> /dev/null; do printf '.' && sleep 1; done"
echo " done"
sleep 1
for container in "${CONTAINERS[@]}"; do
  echo "Initializing database for ${container}..."
  DB_DATA=(`docker-compose run --rm --no-deps $container bash -c 'printf '"'"'"%s" "%s" "%s"'"'"' "${MYSQL_DB}" "${MYSQL_USER}" "${MYSQL_PASS}"'`)
  docker-compose exec db2 bash -c "mysql -uroot --password=\"\${MYSQL_ROOT_PASSWORD}\" -e \"\
    CREATE USER IF NOT EXISTS \\\`${DB_DATA[1]}\\\`@'%' IDENTIFIED BY '${DB_DATA[2]}';\
    CREATE DATABASE IF NOT EXISTS \\\`${DB_DATA[0]}\\\`;\
    GRANT ALL ON \\\`${DB_DATA[0]}\\\`.* TO \\\`${DB_DATA[1]}\\\`@'%';\
    FLUSH PRIVILEGES;\""
    # The following two lines were replaces because mysql use '--skip-name-resolve' making named host useless.
    # CREATE USER IF NOT EXISTS \\\`${DB_DATA[1]}\\\`@'$container' IDENTIFIED BY '${DB_DATA[2]}';\
    # GRANT ALL ON \\\`${DB_DATA[0]}\\\`.* TO \\\`${DB_DATA[1]}\\\`@'$container';\
  docker-compose exec db2 bash -c "mysql -uroot --password=\"\${MYSQL_ROOT_PASSWORD}\" -e \"\
    FLUSH PRIVILEGES;\""
  docker-compose run --rm --no-deps $container bash -c "if [ -f /var/www/html/artisan ]; then /usr/bin/php -d hhvm.jit=0 /var/www/html/artisan --force migrate; else echo \"artisan not found, skipping migration for $container\"; fi"
done
[ -z "$DB_RUNNING" ] && docker-compose down
