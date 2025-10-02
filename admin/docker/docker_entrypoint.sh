#!/bin/sh

if [ "$DEV_RUN" = "true" ]; then
	function watch_locales() {
		echo "Watching locales for changes..."
		cmd="uv run /scripts/build_locales.py --locale-path=/config/locales --locale-override-path=/config/locale_overrides --output-json=./src/i18n/generated_locales --output-ts-type-definitions=./src/i18n/locales.ts --default-locale=en --modules admin common"
		$cmd || true
		while inotifywait -qq -r -e modify,create,delete /config/locales /config/locale_overrides /scripts/build_locales.py; do
			echo "Updating locales"
			sleep 0.05
			$cmd || true
		done
	}

	mkdir -p /work/dist/js
	echo \
	"var config = {
		apiBasePath: \"${HOST_BACKEND}\",
		apiVersion: \"1.0\",
		pagination: {
			pageSize: 25,
		},
	}" > /work/dist/js/config.js;

	watch_locales &
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
