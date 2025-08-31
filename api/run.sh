#!/bin/bash
set -e

GUNICORN_FLAGS=""
GUNICORN_WORKERS="8"

if [ "$DEV_RUN" = "true" ]; then
    echo "running in devel mode"
    GUNICORN_FLAGS=" --reload"
    GUNICORN_WORKERS="2"
fi

if [ "$TEST" = "true" ]; then
    echo "running in test mode"
    GUNICORN_WORKERS="2"
fi

echo "initializing and migrating db"
python3 ./init_db.py

exec gunicorn ${GUNICORN_FLAGS} --access-logfile - --log-level info --error-logfile - --worker-class gevent --workers=${GUNICORN_WORKERS} -b :80 api:app
