#!/bin/sh

chown -R nginx:nginx /var/www/html

BACKEND_HOST=${HOST_BACKEND#*://}
BACKEND_PROTOCOL=${HOST_BACKEND%${BACKEND_HOST}}

echo \
"var config = {
	apiBasePath: \"${BACKEND_PROTOCOL:-https://}${BACKEND_HOST}\",
	apiVersion: \"1.0\",
	pagination: {
		pageSize: 25,
	},
}" > /var/www/html/js/config.js

nginx -g 'daemon off;'
