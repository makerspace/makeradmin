#!/bin/bash
DB_RUNNING=`docker-compose ps -q db2`
[ -z "$DB_RUNNING" ] && docker-compose up -d db2
docker-compose exec db2 bash -c "while ! mysqladmin ping --silent; do echo 'waiting for database' && sleep 1; done"
docker-compose run --rm --no-deps api-gateway /usr/bin/php /var/www/html/artisan --force migrate
docker-compose run --rm --no-deps membership /usr/bin/php /var/www/html/artisan --force migrate
docker-compose run --rm --no-deps messages /usr/bin/php /var/www/html/artisan --force migrate
docker-compose run --rm --no-deps sales /usr/bin/php /var/www/html/artisan --force migrate
docker-compose run --rm --no-deps economy /usr/bin/php /var/www/html/artisan --force migrate
[ -z "$DB_RUNNING" ] && docker-compose down
