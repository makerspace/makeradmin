#!/bin/bash
set -e
# Wait for database to be ready
./wait-for "$MYSQL_HOST"
# Wait for api-gateway to be ready
./wait-for api-gateway:80

python3 migrate.py --assert-up-to-date
# Exec replaces the shell with the service process which among other things allows signals to be sent directly to the service (e.g when docker wants to stop the container)
exec gunicorn -b :80 rfid:instance.app