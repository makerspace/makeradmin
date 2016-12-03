#!/bin/bash

# Make sure the webserver have write permissions
chown -R www-data:www-data /var/www/html/storage/
chown -R www-data:www-data /var/www/html/bootstrap/cache/

shutdown() {
	echo Shutting down service
	/usr/local/bin/php /var/www/html/artisan service:unregister
	kill -QUIT -`cat /var/run/php-fpm.pid`
	kill -QUIT -`cat /var/run/nginx.pid`
	exit 0
}

# Unregister the service when the script is shut down
trap shutdown SIGHUP SIGINT SIGTERM

# Start php-fpm in background
/usr/local/sbin/php-fpm -D

# Register the service immediately
/usr/local/bin/php /var/www/html/artisan service:register

# Start web server and let it take focus
nginx

# Sleep forever (...or at least until the timestamp overflows :)
# Note: We need to have the "& wait" to be able to trap signals while the sleep is running
sleep inf & wait