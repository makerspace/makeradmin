#!/bin/bash
set -e
# Wait for database to be ready
./wait-for "$MYSQL_HOST"
# Wait for api-gateway to be ready
./wait-for api-gateway:80

python3 migrate.py --assert-up-to-date

function refresh() {
	# the OR is to ensure that the whole script won't exit even if the sass translation threw an error
	sass scss/style.scss static/style.css || true
}

function refresh_ts() {
	# the OR is to ensure that the whole script won't exit even if the program threw an error
	(cd ts && ./build.sh) || true
}

refresh

GUNICORN_FLAGS=""

if [ "$APP_DEBUG" == "true" ]; then
	GUNICORN_FLAGS=" --reload"
	function watch_sass() {
		echo "Starting sass watch process"
		while inotifywait -qq -r -e modify,create,delete scss; do
			echo "Updating stylesheets"
			sleep 0.1
			refresh
		done
	}
	watch_sass&
	function watch_ts() {
		echo "Starting typescript watch process"
		while inotifywait -qq -r -e modify,create,delete ts; do
			echo "Updating typescript"
			sleep 0.1
			refresh_ts
		done
	}
	watch_ts&
fi

# Exec replaces the shell with the service process which among other things allows signals to be sent directly to the service (e.g when docker wants to stop the container).
# Note: for some reason the workers seem to sometimes get blocked by persistent connections
# (many browsers keep persistent connections to servers just in case they need them later).
# The gthread worker class should help with this, but it doesn't always seem to work for some reason.
# However running the servers behind nginx (and using the sync class) resolves all problems
# as nginx handles all the persistent connections.
# --log-level=DEBUG
exec gunicorn $GUNICORN_FLAGS --worker-class sync --workers=3 -b :80 frontend:instance.app&
exec gunicorn $GUNICORN_FLAGS --worker-class sync --workers=1 -b :8000 backend:instance.app
