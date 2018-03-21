FROM ubuntu:latest

RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:jonathonf/python-3.6
RUN apt-get update && apt-get install -y --no-install-recommends curl python3.6
RUN curl https://bootstrap.pypa.io/get-pip.py | python3.6
RUN pip3 install --upgrade pip
RUN pip3 install setuptools
RUN pip3 install flask flask-compress fuzzywuzzy jsonpickle PyMySQL python-dateutil requests

# Add all the lumen files
RUN mkdir -p /var/www/service/
ADD ./src /var/www/service/

EXPOSE 80

WORKDIR "/var/www/service"
CMD ["./run.sh"]