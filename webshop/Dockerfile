FROM makeradmin/servicebase_python:1.0

RUN apt-get install -y python3-mysqldb inotify-tools wget npm

RUN wget https://github.com/sass/dart-sass/releases/download/1.3.0/dart-sass-1.3.0-linux-x64.tar.gz --quiet -O sass.tar.gz && tar -xf sass.tar.gz && rm sass.tar.gz
ENV PATH="/dart-sass:${PATH}"

# Install javascript dependencies
COPY src/package-lock.json /var/www/service/package-lock.json
COPY src/package.json /var/www/service/package.json
RUN cd /var/www/service; npm install
# Install typescript compiler and bundler (need to be command line tools)
RUN npm install -g typescript rollup

COPY src /var/www/service/

# Build typescript
RUN cd /var/www/service/ts; ./build.sh

EXPOSE 80

WORKDIR "/var/www/service"
CMD ["./run.sh"]
