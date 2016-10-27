#!/bin/bash

# Make sure the webserver have write permissions
chown -R www-data:www-data /var/www/html/storage/
chown -R www-data:www-data /var/www/html/bootstrap/cache/

# Start php-fpm and web server
/usr/local/sbin/php-fpm -D
nginx -g "daemon off;"
