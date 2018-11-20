FROM python:3.7-alpine

RUN apk update && apk add bash netcat-openbsd less curl build-base python3-dev libffi-dev libressl-dev && rm -rf /var/cache/apk/*

COPY requirements.txt /tmp

RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /work/

COPY run.sh /work/run.sh

COPY src /work/src

WORKDIR "/work"
