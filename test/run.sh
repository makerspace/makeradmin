#!/bin/bash

function wait_for {
    local command="$*"
    echo "wait_for '${command}'"
    for i in $(seq 1 100); do
        if ${command}; then
            echo "wait_for '${command}' complete"
            return
        fi
        sleep 0.2
    done
    echo "wait_for '${command}' timed out"
    exit 1
}

wait_for nc -z db2 3306
wait_for nc -z $APIGATEWAY 80
wait_for nc -z admin 80
wait_for nc -z public 80
wait_for nc -z selenium 4444
wait_for curl --silent --fail --output /dev/null http://$APIGATEWAY:80/webshop/product_data

if [ -z "$TEST_PARALELLISM" ]; then
    TEST_PARALELLISM="auto"
fi

set -e
set -x

rm -rf /work/.test/selenium-screenshots

cd /work/src

python3 -m pytest . --workers $TEST_PARALELLISM -ra
