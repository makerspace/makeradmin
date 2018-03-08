#!/bin/bash

mkdir -p /var/www/html/storage
mkdir -p /var/www/html/bootstrap/cache

# Make sure the webserver have write permissions
chown -R www-data:www-data /var/www/html/storage/
chown -R www-data:www-data /var/www/html/bootstrap/cache/

# Start HHVM
/usr/bin/hhvm -vServer.AllowRunAsRoot=1 -m server -c /etc/hhvm/server.ini -c /etc/hhvm/site.ini
