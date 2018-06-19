FROM makeradmin/servicebase_python:1.0

RUN apt-get install -y python3-mysqldb inotify-tools wget
RUN pip3 install stripe

RUN wget https://github.com/sass/dart-sass/releases/download/1.3.0/dart-sass-1.3.0-linux-x64.tar.gz --quiet -O sass.tar.gz && tar -xf sass.tar.gz && rm sass.tar.gz
ENV PATH="/dart-sass:${PATH}"

COPY src /var/www/service/

EXPOSE 80

WORKDIR "/var/www/service"
CMD ["./run.sh"]
