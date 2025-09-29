FROM python:3.11-alpine@sha256:5d769f990397afbb2aca24b0655e404c0f2806d268f454b052e81e39d87abf42

RUN apk update \
    && apk add \
       bash \
       netcat-openbsd \
       less \
       curl \
       zlib-dev \
       jpeg-dev \
       build-base \
       python3-dev \
       libffi-dev \
       libressl-dev \
       linux-headers \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /work/ && mkdir -p /work/logs

VOLUME /work/logs

COPY default-product-image.png /work

COPY requirements.txt /work
COPY --from=config messages /config/messages

RUN pip install -U pip
RUN pip install -r /work/requirements.txt

COPY run.sh dispatch_emails.sh accessy_syncer.sh /work/

COPY src /work/src

EXPOSE 80

WORKDIR "/work/src"

CMD ["/work/run.sh"]
