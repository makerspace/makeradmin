from logging import getLogger

import redis

logger = getLogger("redis")

try:
    redis_connection = redis.Redis(host="redis", port=6379, db=0, socket_connect_timeout=5)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")

if not redis_connection.ping():
    logger.error("Failed to ping Redis")
