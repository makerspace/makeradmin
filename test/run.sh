#!/bin/bash

function wait_for {
    local command="$*"
    for i in $(seq 1 100); do
        if ${command}; then
            return
        fi
        sleep 0.2
    done
    echo "wait for '${command} timed out"
    exit 1
}

wait_for nc -z db2 3306
wait_for nc -z admin 80
wait_for nc -z public 80
wait_for curl --silent --fail --output /dev/null http://api-gateway:80/webshop/product_data

set -e

cd /work

pytest .
