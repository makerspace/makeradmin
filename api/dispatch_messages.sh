#!/bin/bash
set -e

echo "starting message dispatcher"

function cleanup() {
    if [ -n "$DISPATCHER_PID" ]; then
        kill "$DISPATCHER_PID"
        wait "$DISPATCHER_PID"
    fi
    exit 0
}

function watch_and_restart() {
    trap 'cleanup' SIGINT SIGTERM SIGQUIT

    python3 ./dispatch_messages.py &
    DISPATCHER_PID=$!

    echo "Watching message modules for changes..."

    while true; do
        # Run inotifywait as a background process so trap handlers can run at any time.
        # This ensures that if a user tries to stop the docker container, it will stop quickly.
        inotifywait -qq -r -e modify,create,delete /work/src/messages /work/src/slack /work/src/quiz /config/messages /work/src/i18n --exclude '__pycache__'&
        wait $!
        sleep 0.4
        if [ -n "$DISPATCHER_PID" ]; then
            echo "Restarting dispatch_messages.py"
            kill $DISPATCHER_PID
            wait $DISPATCHER_PID
            python3 ./dispatch_messages.py &
            DISPATCHER_PID=$!
        fi
    done
}

if [ "$DEV_RUN" = "true" ]; then
    echo "running in devel mode"
    watch_and_restart
else
    exec python3 ./dispatch_messages.py
fi
