#!/bin/bash
docker-compose build && docker-compose down --remove-orphans && ./start.sh

