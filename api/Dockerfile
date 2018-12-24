FROM python:3.7-alpine

RUN apk update && apk add bash netcat-openbsd less curl build-base python3-dev libffi-dev libressl-dev linux-headers && rm -rf /var/cache/apk/*

RUN mkdir -p /work/

COPY requirements.txt /work

RUN pip install -r /work/requirements.txt

COPY run.sh /work/

COPY src /work/src

EXPOSE 80

WORKDIR "/work/src"

CMD ["/work/run.sh"]
