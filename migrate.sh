#!/bin/bash
find -path "*/docker/artisan" | while read f; do
	echo $f
	source $(echo "$f" | sed -e "s/artisan/config/")
	docker exec $CONTAINER_NAME /usr/bin/php /var/www/html/artisan --force migrate
done
