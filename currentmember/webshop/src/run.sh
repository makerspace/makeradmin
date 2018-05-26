#!/bin/bash
set -e
# Wait for database to be ready
./wait-for "$MYSQL_HOST"
# Wait for api-gateway to be ready
./wait-for api-gateway:80

python3 migrate.py --assert-up-to-date

function refresh() {
	sass static/style.scss static/style.css
}

refresh

if [ "$APP_DEBUG" == "true" ]; then
	function watch_sass() {
		echo "Starting sass watch process"
		while inotifywait -qq -r -e modify,create,delete static; do
			echo "Updating stylesheets"
			sleep 0.1
			refresh
		done
	}
	watch_sass&
fi

# Exec replaces the shell with the service process which among other things allows signals to be sent directly to the service (e.g when docker wants to stop the container)
exec python3 frontend.py&
exec python3 backend.py