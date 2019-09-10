#!/bin/bash
set -e
set -v
docker-compose up -d db2
docker-compose exec db2 bash -c "mysql -uroot -p\${MYSQL_ROOT_PASSWORD} makeradmin -e \"\
UPDATE migrations SET name='2018-12-23T23:26:53_initial' WHERE id=1 AND service='core' AND name='0001_initial';\
UPDATE migrations SET name='2018-12-24T00:16:04_initial' WHERE id=1 AND service='membership' AND name='0001_initial';\
UPDATE migrations SET name='2019-03-18T20:53:38_remove_excessive_permissions' WHERE id=2 AND service='membership' AND name='0002_remove_excessive_permissions';\
UPDATE migrations SET name='2019-04-14T15:45:07_add_box' WHERE id=3 AND service='membership' AND name='0003_add_box';\
UPDATE migrations SET name='2018-12-24T00:16:06_initial' WHERE id=1 AND service='messages' AND name='0001_initial';\
UPDATE migrations SET name='2019-06-02T21:27:50_rename_everything' WHERE id=2 AND service='messages' AND name='0002_rename_everything';\
UPDATE migrations SET name='2018-12-24T00:16:05_initial' WHERE id=1 AND service='shop' AND name='0001_initial';\""

