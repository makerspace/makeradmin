FROM python:3.9-alpine

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

RUN pip install -r /work/requirements.txt

COPY run.sh dispatch_emails.sh /work/

COPY src /work/src

EXPOSE 80

WORKDIR "/work/src"

CMD ["/work/run.sh"]
