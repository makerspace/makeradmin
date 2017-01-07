#!/bin/bash

# Make sure the webserver have write permissions
chown -R www-data:www-data /var/www/html/storage/
chown -R www-data:www-data /var/www/html/bootstrap/cache/

# Start HHVM
/usr/bin/hhvm -m server -c /etc/hhvm/server.ini -c /etc/hhvm/site.ini