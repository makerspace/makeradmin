#!/bin/bash
set -e

python3 ./migrate.py

GUNICORN_FLAGS=""

if [ "$APP_DEBUG" = "true" ]; then
    echo "running app in devel mode"
    GUNICORN_FLAGS=" --reload"
fi

# Note: for some reason the workers seem to sometimes get blocked by persistent connections
# (many browsers keep persistent connections to servers just in case they need them later).
# The gthread worker class should help with this, but it doesn't always seem to work for some reason.
# However running the servers behind nginx (and using the sync class) resolves all problems
# as nginx handles all the persistent connections.
echo "starting gunicorn"
exec gunicorn ${GUNICORN_FLAGS} --access-logfile - --worker-class sync --workers=4 -b :80 api:app
