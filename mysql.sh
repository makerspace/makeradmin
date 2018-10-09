#!/bin/bash
set -e
db=`docker-compose ps -q db2`
docker exec -it $db bash -c "mysql -uroot --password=\"\${MYSQL_ROOT_PASSWORD}\" $*"

