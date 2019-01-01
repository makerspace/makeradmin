import sys
from logging import getLogger, basicConfig, INFO

basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)

logger = getLogger('makeradmin')

# TODO BM Double check all sql queries everywhere.
getLogger('sqlalchemy.engine').setLevel(INFO)
