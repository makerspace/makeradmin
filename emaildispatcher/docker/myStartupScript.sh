#!/bin/bash
set -e
# Wait for database to be ready
/usr/local/myscripts/wait-for "$MYSQL_HOST"
# Wait for api-gateway to be ready
/usr/local/myscripts/wait-for api-gateway:80

exec /usr/bin/php -d hhvm.max_execution_time=0 /var/www/html/artisan service:send
