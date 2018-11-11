#!/bin/bash
set -e
docker-compose exec db2 bash -c "mysql -uroot -p\${MYSQL_ROOT_PASSWORD} makeradmin"
