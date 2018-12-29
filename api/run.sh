#!/bin/bash
set -e

GUNICORN_FLAGS=""
WORKERS="4"

if [ "$APP_DEBUG" = "true" ]; then
    echo "running in devel mode"
    GUNICORN_FLAGS=" --reload"
    WORKERS="1"
fi

echo "migrating"
python3 ./migrate.py

# Note: for some reason the workers seem to sometimes get blocked by persistent connections
# (many browsers keep persistent connections to servers just in case they need them later).
# The gthread worker class should help with this, but it doesn't always seem to work for some reason.
# However running the servers behind nginx (and using the sync class) resolves all problems
# as nginx handles all the persistent connections.
echo "starting gunicorn"

exec gunicorn ${GUNICORN_FLAGS} --access-logfile - --worker-class sync --workers=${WORKERS} -b :80 api:app
