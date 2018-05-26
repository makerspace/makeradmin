#!/bin/bash
set -e
# Wait for api-gateway to be ready
/usr/local/myscripts/wait-for api-gateway:80


# Not sure if these directories are needed, but let's create them anyway
mkdir -p /var/www/html/storage/
mkdir -p /var/www/html/bootstrap/cache/

# Make sure the webserver have write permissions
chown -R www-data:www-data /var/www/html/storage/
chown -R www-data:www-data /var/www/html/bootstrap/cache/

shutdown() {
	echo Shutting down service
	/usr/bin/php /var/www/html/artisan service:unregister
	kill -QUIT `cat /var/run/hhvm/pid`
	echo Killed HHVM
	exit 0
}

# Unregister the service when the script is shut down
trap shutdown SIGHUP SIGINT SIGTERM

# Register the service immediately
/usr/bin/php /var/www/html/artisan service:register

# Start HHVM as a background process
echo "Starting HHVM"
/usr/bin/hhvm -vServer.AllowRunAsRoot=1 -m daemon -c /etc/hhvm/server.ini -c /etc/hhvm/site.ini &

# Sleep forever (...or at least until the timestamp overflows :)
# Note: We need to have the "& wait" to be able to trap signals while the sleep is running
echo "Sleeping"
sleep inf & wait
