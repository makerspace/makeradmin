#!/bin/bash
set -e

echo "starting emaildispatcher"

function cleanup() {
    if [ -n "$EMAIL_PID" ]; then
        kill "$EMAIL_PID"
        wait "$EMAIL_PID"
    fi
    exit 0
}

function watch_and_restart() {
    trap 'cleanup' SIGINT SIGTERM SIGQUIT

    python3 ./dispatch_emails.py &
    EMAIL_PID=$!

    echo "Watching locales for changes..."

    while true; do
        # If we are in dev mode, then the API container is also in dev mode and will update the locale for us.
        # Just wait a bit to let that happen. This avoids having two processes trying to update the same files.
        #
        # We run inotifywait as a background process and wait for it to finish because trap handlers (e.g. SIGTERM) will never run
        # while a foreground process is running. By running inotifywait in the background, we allow trap handlers to run at any time.
        # This ensures that if a user tries to stop the docker container, it will stop quickly.
        inotifywait -qq -r -e modify,create,delete /work/src/i18n /config/messages --exclude '__pycache__'&
        wait $!
        sleep 0.4
        if [ -n "$EMAIL_PID" ]; then
            echo "Restarting dispatch_emails.py"
            kill $EMAIL_PID
            wait $EMAIL_PID
            python3 ./dispatch_emails.py &
            EMAIL_PID=$!
        fi
    done
}

if [ "$DEV_RUN" = "true" ]; then
    echo "running in devel mode"
    watch_and_restart
else
    exec python3 ./dispatch_emails.py
fi
