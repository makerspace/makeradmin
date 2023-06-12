#!/bin/bash
docker compose build && docker compose -f docker-compose.yml -f docker-compose.prod.yml  down --remove-orphans && ./start.sh

echo "sleeping a long long time then restarting the reverse proxy to make certs work again"
sleep 12
docker restart reverse-proxy
