#!/bin/sh

if [ "$DEV_RUN" = "true" ]; then
	mkdir -p /work/dist/js
	echo \
	"var config = {
		apiBasePath: \"${HOST_BACKEND}\",
		apiVersion: \"1.0\",
		pagination: {
			pageSize: 25,
		},
	}" > /work/dist/js/config.js
	exec npm run --silent dev
else
	mkdir -p /var/www/html/js;
	echo \
	"var config = {
		apiBasePath: \"${HOST_BACKEND}\",
		apiVersion: \"1.0\",
		pagination: {
			pageSize: 25,
		},
	}" > /var/www/html/js/config.js
	chown -R nginx:nginx /var/www/html
	exec nginx -g 'daemon off;'
fi
