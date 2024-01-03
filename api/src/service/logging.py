import sys
from logging import INFO, basicConfig, getLogger

basicConfig(
    format="%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s",
    stream=sys.stderr,
    level=INFO,
)

logger = getLogger("makeradmin")

# getLogger('sqlalchemy.engine').setLevel(INFO)
