FROM python:3.7-alpine

RUN apk update \
    && apk add \
        bash \
        netcat-openbsd \
        less \
        curl \
        build-base \
        python3-dev \
        libffi-dev \
        libressl-dev \
        chromium \
        xvfb \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /work/

WORKDIR /work

RUN wget -q https://chromedriver.storage.googleapis.com/2.44/chromedriver_linux64.zip

RUN unzip chromedriver_linux64.zip

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY run.sh .

COPY src ./src

RUN adduser -s /bin/bash -D -u 1000 pytest

USER pytest
