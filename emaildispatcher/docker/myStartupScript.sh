#!/bin/bash
exec /usr/bin/php -d hhvm.max_execution_time=0 /var/www/html/artisan service:send
