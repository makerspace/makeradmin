#!/bin/bash

shutdown() {
	echo Shutting down service
#	/usr/local/bin/php /var/www/html/artisan service:unregister
#	kill -QUIT -`cat /var/run/php-fpm.pid`
#	kill -QUIT -`cat /var/run/nginx.pid`
	exit 0
}

# Unregister the service when the script is shut down
#trap shutdown SIGHUP SIGINT SIGTERM

# Infinite loop
#while true
#do
	# Executing the send queue
	echo "Executing the send queue"
	/usr/local/bin/php /var/www/html/artisan service:send

	# Note: We need to have the "& wait" to be able to trap signals while the sleep is running
#	echo "Sleeping 10 seconds"
#	sleep 10 & wait
#done