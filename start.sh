#!/bin/bash

./create_connect.sh && \
docker-compose -f docker-compose.yml up -d
