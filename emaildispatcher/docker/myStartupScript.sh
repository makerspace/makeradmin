#!/bin/bash
set -e

# Wait for api gateway to be ready
/usr/local/myscripts/wait-for "$APIGATEWAY:80"

exec php /var/www/html/artisan service:send
