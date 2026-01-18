FROM node:lts-alpine3.22@sha256:d2166de198f26e17e5a442f537754dd616ab069c47cc57b889310a717e0abbf9

RUN apk add --no-cache tzdata && rm -rf /var/cache/apk/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV TZ=Europe/Stockholm

RUN mkdir -p /work/src && mkdir -p /work/dist/js

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY admin/webpack.config.js admin/tsconfig.json admin/package.json admin/package-lock.json /work/

WORKDIR /work

RUN npm ci --install-links=false

COPY frontend_common /frontend_common
COPY config /config
COPY scripts/build_locales.py /scripts/
COPY admin/src/ /work/src
COPY admin/jestSetup.js /work/

RUN npm run build
RUN echo tsc --version

RUN uv run /scripts/build_locales.py --locale-path=/config/locales --locale-override-path=/config/locale_overrides --output-json=/work/src/i18n/generated_locales --output-ts-type-definitions=/work/src/i18n/locales.ts --default-locale=en --modules admin common

FROM nginx:alpine@sha256:74175cf34632e88c6cfe206897cbfe2d2fecf9bf033c40e7f9775a3689e8adc7

# Configuration file for nginx
COPY admin/docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
RUN mkdir -p /var/www/html
COPY --from=0 /work/dist/ /var/www/html

EXPOSE 80

COPY admin/docker/docker_entrypoint.sh /usr/local/myscripts/docker_entrypoint.sh
CMD ["/usr/local/myscripts/docker_entrypoint.sh"]
