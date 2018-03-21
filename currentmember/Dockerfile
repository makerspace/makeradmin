FROM ubuntu:latest

RUN apt-get update && apt-get install -y --no-install-recommends curl python3 python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install setuptools
RUN pip3 install flask flask-compress fuzzywuzzy jsonpickle PyMySQL python-dateutil requests

# Add all the source files
RUN mkdir -p /var/www/service/
ADD ./src /var/www/service/

EXPOSE 80

WORKDIR "/var/www/service"
CMD ["./run.sh"]