#!/bin/bash
set -e

GUNICORN_FLAGS=""
GUNICORN_WORKERS="8"

if [ "$DEV_RUN" = "true" ]; then
    echo "running in devel mode"
    GUNICORN_FLAGS=" --reload"
    GUNICORN_WORKERS="2"
fi

echo "initializing and migrating db"
python3 ./init_db.py

echo "starting gunicorn"
exec gunicorn ${GUNICORN_FLAGS} --access-logfile - --log-level debug --error-logfile - --worker-class sync --workers=${GUNICORN_WORKERS} -b :80 api:app
