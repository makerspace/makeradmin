#!/bin/bash

docker-compose -f docker-compose.yml up --no-start api admin public && \
docker network connect makeradmin-bridge `docker-compose ps -q api` && \
docker network connect makeradmin-bridge `docker-compose ps -q admin` && \
docker network connect makeradmin-bridge `docker-compose ps -q public`

