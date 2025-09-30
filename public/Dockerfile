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

RUN pip3 install flask gunicorn pyjson5

RUN mkdir -p /work/src && mkdir -p /work/dist/js

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY ./package.json ./package-lock.json /work/

WORKDIR /work

COPY --from=frontend_common . /frontend_common
RUN npm ci --install-links=false

COPY --from=scripts build_locales.py /scripts/
COPY --from=config . /config
COPY ./webpack.config.js /work/

COPY ts /work/ts

COPY static /work/static

COPY scss /work/scss

COPY src /work/src

COPY run.sh /work/run.sh

RUN npm exec sass scss/style.scss static/style.css

RUN python3 /scripts/build_locales.py --locale-path=/config/locales --locale-override-path=/config/locale_overrides --output-json=/work/ts/generated_locales --output-ts-type-definitions=/work/ts/locales.ts --default-locale=en --modules member_portal common

ARG DEV_BUILD

RUN test "$DEV_BUILD" = "true" || npm run build

EXPOSE 80

CMD ["./run.sh"]
