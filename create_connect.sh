#!/bin/bash

docker compose -f docker-compose.yml -f docker-compose.prod.yml up --no-start api admin public && \
docker network connect makeradmin-bridge "$(docker compose ps --all -q api)" && \
docker network connect makeradmin-bridge "$(docker compose ps --all -q admin)" && \
docker network connect makeradmin-bridge "$(docker compose ps --all -q public)"
