#!/bin/bash
CONTAINERS=( api-gateway membership messages sales economy )
DB_RUNNING=`docker-compose ps -q db2`
[ -z "$DB_RUNNING" ] && docker-compose up -d db2
docker-compose exec db2 bash -c "while ! mysqladmin ping --silent; do echo 'waiting for database' && sleep 1; done"
for container in "${CONTAINERS[@]}"; do
  docker-compose run --rm --no-deps $container /usr/bin/php /var/www/html/artisan --force migrate
done
[ -z "$DB_RUNNING" ] && docker-compose down

exit 0;
