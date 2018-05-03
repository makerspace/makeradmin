FROM ubuntu:latest

RUN apt-get update && apt-get install -y curl python3 python3-pip python3-mysqldb inotify-tools wget
RUN pip3 install --upgrade pip
RUN pip3 install setuptools
RUN pip3 install flask flask-compress fuzzywuzzy jsonpickle PyMySQL python-dateutil requests mygrations stripe

# Add all the source files
RUN mkdir -p /var/www/service/

RUN wget https://github.com/sass/dart-sass/releases/download/1.3.0/dart-sass-1.3.0-linux-x64.tar.gz --quiet -O sass.tar.gz && tar -xf sass.tar.gz && rm sass.tar.gz
ENV PATH="/dart-sass:${PATH}"

COPY webshop/src /var/www/service/
COPY common /var/www/service/

EXPOSE 80

WORKDIR "/var/www/service"
CMD ["./run.sh"]
