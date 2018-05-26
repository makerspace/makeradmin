#!/bin/bash

mkdir -p /var/www/html/storage
mkdir -p /var/www/html/bootstrap/cache

# Make sure the webserver have write permissions
chown -R www-data:www-data /var/www/html/storage/
chown -R www-data:www-data /var/www/html/bootstrap/cache/

shutdown() {
	echo Shutting down gateway
	kill -QUIT `cat /var/run/hhvm/pid`
	exit 0
}

# Stop HHVM gracefully when the script is shut down
trap shutdown SIGHUP SIGINT SIGTERM

# Disable the JIT because HHVM starts up really slowly with a JIT and this script is very short
/usr/bin/php -d hhvm.jit=0 /var/www/html/artisan db:init

# Start HHVM
/usr/bin/hhvm -vServer.AllowRunAsRoot=1 -m server -c /etc/hhvm/server.ini -c /etc/hhvm/site.ini &

# Sleep forever (...or at least until the timestamp overflows :)
# Note: We need to have the "& wait" to be able to trap signals while the sleep is running
echo "Sleeping"
sleep inf & wait
