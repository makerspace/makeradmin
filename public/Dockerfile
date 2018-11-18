FROM ubuntu:latest

RUN apt-get update && apt-get install -y curl python3 python3-pip netcat

RUN apt-get install -y inotify-tools wget npm curl

RUN wget https://github.com/sass/dart-sass/releases/download/1.3.0/dart-sass-1.3.0-linux-x64.tar.gz --quiet -O sass.tar.gz && tar -xf sass.tar.gz && rm sass.tar.gz
ENV PATH="/dart-sass:${PATH}"

RUN pip3 install flask gunicorn

# Install javascript dependencies
COPY package-lock.json /var/www/service/package-lock.json
COPY package.json /var/www/service/package.json
RUN cd /var/www/service; npm install
# Install typescript compiler and bundler (need to be command line tools)
RUN npm install -g typescript rollup

# Copy typescript and build it
# Do this before copying the rest of the sources to make rebuilding quicker if no .ts files are changed
COPY ts /var/www/service/ts

COPY static /var/www/service/static

# Build typescript
RUN cd /var/www/service/ts; ./build.sh

COPY run.sh /var/www/service/run.sh
COPY public.py /var/www/service/public.py
COPY templates /var/www/service/templates

EXPOSE 80

WORKDIR "/var/www/service"
CMD ["./run.sh"]
