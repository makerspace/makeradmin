FROM python:3.11-alpine@sha256:5d769f990397afbb2aca24b0655e404c0f2806d268f454b052e81e39d87abf42

RUN apk update \
	&& apk add \
	less \
	bash \
	build-base \
	curl \
	python3-dev \
	netcat-openbsd \
	inotify-tools \
	wget \
	npm \
	curl \
	&& rm -rf /var/cache/apk/*

RUN npm install -g npm@9.2.0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir -p /work/src && mkdir -p /work/dist/js

# Install Python dependencies for the public server
# (Only 3 simple packages for serving static files)
RUN uv pip install --system --no-cache flask gunicorn pyjson5

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY public/package.json public/package-lock.json /work/

WORKDIR /work

COPY frontend_common /frontend_common
RUN npm ci --install-links=false

COPY scripts/build_locales.py /scripts/
COPY config /config
COPY public/webpack.config.js /work/

COPY public/ts /work/ts

COPY public/static /work/static

COPY public/scss /work/scss

COPY public/src /work/src

COPY public/run.sh /work/run.sh

RUN npm exec sass scss/style.scss static/style.css

RUN python3 /scripts/build_locales.py --locale-path=/config/locales --locale-override-path=/config/locale_overrides --output-json=/work/ts/generated_locales --output-ts-type-definitions=/work/ts/locales.ts --default-locale=en --modules member_portal common

ARG DEV_BUILD

RUN test "$DEV_BUILD" = "true" || npm run build

EXPOSE 80

CMD ["./run.sh"]
