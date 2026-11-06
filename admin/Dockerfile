FROM node:24-alpine3.24@sha256:a34ab6d7f6f4813f4d0c5469d74685604b962fbdbf5793a7bc7b4998ecb867c8

RUN apk add --no-cache tzdata && rm -rf /var/cache/apk/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# pyjson5 ships no wheels for the newest CPython on release, and this image has no C++ compiler to build it.
ENV UV_PYTHON=3.14
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
COPY admin/dist/ /work/dist/

RUN npm run build
RUN echo tsc --version

RUN uv run /scripts/build_locales.py --locale-path=/config/locales --locale-override-path=/config/locale_overrides --output-json=/work/src/i18n/generated_locales --output-ts-type-definitions=/work/src/i18n/locales.ts --default-locale=en --modules admin common

FROM nginx:alpine3.24@sha256:713fc2ebfd92e8217db451477182ee91944b123d2b1ee9fd5a8c6e91ca6c3a11

# Configuration file for nginx
COPY admin/docker/nginx_default_host /etc/nginx/conf.d/default.conf

# Add files to web root
RUN mkdir -p /var/www/html
COPY --from=0 /work/dist/ /var/www/html

EXPOSE 80

COPY admin/docker/docker_entrypoint.sh /usr/local/myscripts/docker_entrypoint.sh
CMD ["/usr/local/myscripts/docker_entrypoint.sh"]
