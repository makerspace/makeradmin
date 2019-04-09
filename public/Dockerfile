FROM ubuntu:latest

RUN apt-get update && apt-get install -y curl python3 python3-pip netcat

RUN apt-get update && apt-get install -y inotify-tools wget npm curl

RUN npm i -g npm

RUN wget https://github.com/sass/dart-sass/releases/download/1.3.0/dart-sass-1.3.0-linux-x64.tar.gz --quiet -O sass.tar.gz && tar -xf sass.tar.gz && rm sass.tar.gz
ENV PATH="/dart-sass:${PATH}"

RUN pip3 install flask gunicorn

RUN mkdir -p /work/src && mkdir -p /work/dist/js

# Copy package file first, to avoid having to install dependencies every time a source file is updated
COPY ./package.json ./package-lock.json /work/

WORKDIR /work

RUN npm install

COPY ./webpack.config.js /work/

COPY ts /work/ts

RUN npm run build

COPY static /work/static

COPY scss /work/scss

RUN /dart-sass/scss scss/style.scss static/style.css || true

COPY src /work/src

COPY run.sh /work/run.sh

EXPOSE 80

WORKDIR "/work"

CMD ["./run.sh"]
