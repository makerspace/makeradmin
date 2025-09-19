#!/bin/sh

chown -R nginx:nginx /var/www/html

echo \
"var config = {
	apiBasePath: \"${HOST_BACKEND}\",
	apiVersion: \"1.0\",
	pagination: {
		pageSize: 25,
	},
}" > /var/www/html/js/config.js

if [ "$DEV_RUN" = "true" ]; then
	exec npm run --silent dev
else
	exec nginx -g 'daemon off;'
fi
