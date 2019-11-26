#!/bin/bash
set -e
set -v
docker-compose up -d db2
docker-compose exec db2 bash -c "mysql -uroot -p\${MYSQL_ROOT_PASSWORD} makeradmin -e \"\
UPDATE migrations SET id=1, name='0001_initial_core' WHERE id=1 AND service='core' AND name='0001_initial';\
UPDATE migrations SET id=5, name='0005_remove_excessive_permissions' WHERE id=2 AND service='membership' AND name='0002_remove_excessive_permissions';\
UPDATE migrations SET id=6, name='0006_add_box' WHERE id=3 AND service='membership' AND name='0003_add_box';\
UPDATE migrations SET id=2, name='0002_initial_membership' WHERE id=1 AND service='membership' AND name='0001_initial';\
UPDATE migrations SET id=4, name='0004_initial_messages' WHERE id=1 AND service='messages' AND name='0001_initial';\
UPDATE migrations SET id=7, name='0007_rename_everything' WHERE id=2 AND service='messages' AND name='0002_rename_everything';\
UPDATE migrations SET id=3, name='0003_initial_shop' WHERE id=1 AND service='shop' AND name='0001_initial';\
UPDATE migrations SET id=8, name='0008_password_reset_token' WHERE id=2 AND service='core' AND name='0002_password_reset_token';\
ALTER TABLE migrations DROP COLUMN service;\""
