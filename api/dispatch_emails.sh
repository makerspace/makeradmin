#!/bin/bash
set -e

echo "starting emaildispatcher"

function watch_and_restart() {
    python3 ./dispatch_emails.py &
    EMAIL_PID=$!

    echo "Watching locales for changes..."

    while true; do
        # If we are in dev mode, then the API container is also in dev mode and will update the locale for us.
        # Just wait a bit to let that happen. This avoids having two processes trying to update the same files.
        inotifywait -qq -r -e modify,create,delete /work/src/i18n /config/messages --exclude '__pycache__'
        sleep 0.4
        if [ -n "$EMAIL_PID" ]; then
            echo "Restarting dispatch_emails.py"
            kill $EMAIL_PID
            echo "Waiting for email dispatcher to exit"
            wait $EMAIL_PID
            echo "Starting new email dispatcher"
            python3 ./dispatch_emails.py &
            EMAIL_PID=$!
            echo "Email dispatcher started with pid $EMAIL_PID"
        fi
    done
}

if [ "$DEV_RUN" = "true" ]; then
    echo "running in devel mode"
    watch_and_restart
else
    exec python3 ./dispatch_emails.py
fi
