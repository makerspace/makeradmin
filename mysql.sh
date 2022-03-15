#!/bin/bash
set -e
docker-compose exec db2 bash -c "mysql --default-character-set=utf8mb4 -uroot -p\${MYSQL_ROOT_PASSWORD} makeradmin"
