#!/bin/bash
docker-compose build && docker-compose -f docker-compose.yml down --remove-orphans && ./start.sh

