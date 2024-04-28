FROM python:3.11-alpine

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

RUN npm i -g npm sass

RUN pip3 install flask flask_babel gunicorn

RUN mkdir -p /work/src && mkdir -p /work/dist/js

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY ./package.json ./package-lock.json /work/

WORKDIR /work

RUN npm ci

COPY ./webpack.config.js /work/

COPY ts /work/ts

COPY static /work/static

COPY scss /work/scss

COPY src /work/src

COPY run.sh /work/run.sh

RUN sass scss/style.scss static/style.css

ARG DEV_BUILD

RUN test "$DEV_BUILD" = "true" || npm run build

EXPOSE 80

CMD ["./run.sh"]
