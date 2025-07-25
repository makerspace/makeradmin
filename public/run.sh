#!/bin/bash
set -e

GUNICORN_FLAGS=""
GUNICORN_PORT=80
GUNICORN_WORKERS=4

function watch_sass() {
    cmd="npm exec sass scss/style.scss static/style.css"
    echo "starting sass watch process"
    $cmd || true
    while inotifywait -qq -r -e modify,create,delete scss; do
        echo "updating stylesheets"
        sleep 0.1
        $cmd || true
    done
}

function watch_locales() {
    echo "starting locales watch process"
    cmd="npx tsx scripts/build_locales.ts"
    $cmd || true
    while inotifywait -qq -r -e modify,create,delete ts/locales; do
        echo "updating locales"
        sleep 0.05
        $cmd || true
    done
}

if [ "$DEV_RUN" = "true" ]; then
        echo "running app in devel mode"
        STATIC_PREFIX_HASH=""
        export STATIC_PREFIX_HASH

        # Set gunicorn to reload on changes in source files.
        GUNICORN_FLAGS=" --reload"
        # Run gunicorn on 81 and the let webpack dev server proxy needed urls from 80.
        GUNICORN_PORT=81
        # Don't need that many workers.
        GUNICORN_WORKERS=1

        # Run watch for sass compilation
        watch_sass &

        # Run watch for locales compilation
        watch_locales &

        # Run webpack dev server.
        npm run dev &
else
    # Calculates a hash based on the hash of every file here
    STATIC_PREFIX_HASH="_$(find . -type f -exec md5sum {} \; | sort -k 2 | md5sum | cut -c 1-6)"
    export STATIC_PREFIX_HASH
    echo "Prefix hash $STATIC_PREFIX_HASH"
fi

# Note: for some reason the workers seem to sometimes get blocked by persistent connections
# (many browsers keep persistent connections to servers just in case they need them later).
# The gthread worker class should help with this, but it doesn't always seem to work for some reason.
# However running the servers behind nginx (and using the sync class) resolves all problems
# as nginx handles all the persistent connections.
echo "starting gunicorn"
exec gunicorn $GUNICORN_FLAGS --access-logfile - --log-level info --error-logfile - --worker-class sync --chdir src --workers=$GUNICORN_WORKERS -b :$GUNICORN_PORT public:app
