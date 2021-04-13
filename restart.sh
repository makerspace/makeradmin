#!/bin/bash
docker-compose build && docker-compose -f docker-compose.yml -f docker-compose.prod.yml  down --remove-orphans && ./start.sh

