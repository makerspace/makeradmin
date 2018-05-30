#!/bin/bash
set -e

# Wait for database to be ready
/usr/local/myscripts/wait-for "$MYSQL_HOST"

mkdir -p /var/www/html/storage
mkdir -p /var/www/html/bootstrap/cache

# Make sure the webserver have write permissions
chown -R www-data:www-data /var/www/html/storage/

shutdown() {
	echo Shutting down gateway
	kill -QUIT `cat /var/run/nginx.pid`
	kill -QUIT `cat /var/run/php/php7.2-fpm.pid`
	exit 0
}

# Unregister the service when the script is shut down
trap shutdown SIGHUP SIGINT SIGTERM

php /var/www/html/artisan db:init

# Start nginx
echo "Starting server"
php-fpm -R
nginx

# Sleep forever (...or at least until the timestamp overflows :)
# Note: We need to have the "& wait" to be able to trap signals while the sleep is running
echo "Sleeping"
sleep inf & wait
