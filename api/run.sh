#!/bin/bash
set -e

function watch_locales() {
    echo "Watching locales for changes..."
    cmd="python3 /scripts/build_locales.py --locale-path=/config/locales/ --locale-override-path=/config/locale_overrides --output-py=/work/src/i18n --default-locale=en --modules admin common"
    $cmd || true
    while inotifywait -qq -r -e modify,create,delete /config/locales /config/locale_overrides /scripts/build_locales.py; do
        echo "Updating locales"
        sleep 0.05
        $cmd || true
    done
}

GUNICORN_FLAGS=""
GUNICORN_WORKERS="8"

if [ "$DEV_RUN" = "true" ]; then
    echo "running in devel mode"
    GUNICORN_FLAGS=" --reload"
    GUNICORN_WORKERS="2"
    watch_locales &
fi

if [ "$TEST" = "true" ]; then
    echo "running in test mode"
    GUNICORN_WORKERS="2"
fi

echo "initializing and migrating db"
python3 ./init_db.py

exec gunicorn ${GUNICORN_FLAGS} --access-logfile - --log-level info --error-logfile - --worker-class sync --workers=${GUNICORN_WORKERS} -b :80 api:app
