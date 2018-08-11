FROM ubuntu:latest

RUN apt-get update && apt-get install -y curl python3 python3-pip netcat
RUN pip3 install --upgrade pip
RUN pip3 install setuptools
COPY requirements.txt /
RUN pip3 install -r /requirements.txt

# Add all the source files
RUN mkdir -p /var/www/service/
COPY . /var/www/service/
