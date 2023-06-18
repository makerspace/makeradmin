#!/bin/bash
CURRENT_TIME=`date +%FT%T+%N`
DB_CONTAINER=`docker compose ps -q db2`
FILEPATH=/tmp/db_${CURRENT_TIME}.sql
EXPORT_PATH=data/db_backup

mkdir -p ${EXPORT_PATH}
docker compose exec db2	bash -c "mysqldump -p\${MYSQL_ROOT_PASSWORD}  --create-options --complete-insert --quote-names makeradmin >> ${FILEPATH}"
echo docker cp ${DB_CONTAINER}:${FILEPATH} ${EXPORT_PATH}
docker cp ${DB_CONTAINER}:${FILEPATH} ${EXPORT_PATH}
docker compose exec db2	bash -c "rm ${FILEPATH}"
