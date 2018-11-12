#!/bin/bash
set -e
# Wait for database to be ready
./wait-for "$MYSQL_HOST"
# Wait for api-gateway to be ready
./wait-for api-gateway:80

GUNICORN_FLAGS=""


if [ "$APP_DEBUG" = "true" ]; then
    echo "Running app in devel mode."
    GUNICORN_FLAGS=" --reload"
fi

# Exec replaces the shell with the service process which among other things allows signals to be sent directly to the service (e.g when docker wants to stop the container)
exec gunicorn $GUNICORN_FLAGS --access-logfile - -b :80 main:app
