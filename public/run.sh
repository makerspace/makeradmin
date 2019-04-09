#!/bin/bash
set -e

function refresh() {
	# the OR is to ensure that the whole script won't exit even if the sass translation threw an error
	sass scss/style.scss static/style.css || true
}

GUNICORN_FLAGS=""

if [ "$APP_DEBUG" = "true" ]; then
	echo "running app in devel mode"
	GUNICORN_FLAGS=" --reload"
	function watch_sass() {
		echo "starting sass watch process"
		while inotifywait -qq -r -e modify,create,delete scss; do
			echo "Updating stylesheets"
			sleep 0.1
			refresh
		done
	}
	

        npm run dev &
fi

# Note: for some reason the workers seem to sometimes get blocked by persistent connections
# (many browsers keep persistent connections to servers just in case they need them later).
# The gthread worker class should help with this, but it doesn't always seem to work for some reason.
# However running the servers behind nginx (and using the sync class) resolves all problems
# as nginx handles all the persistent connections.
# --log-level=DEBUG
echo "starting gunicorn"
exec gunicorn $GUNICORN_FLAGS --access-logfile - --worker-class sync --chdir src --workers=2 -b :80 public:app
