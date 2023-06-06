import sys
import os
import graypy
from logging import getLogger, basicConfig, INFO



basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s',
            stream=sys.stderr, level=INFO)
logger = getLogger('makeradmin')

if(os.environ.get('GRAYLOG_HOST') is not None and os.environ.get('GRAYLOG_PORT') is not None):
    graypy_handler = graypy.GELFUDPHandler(os.environ.get('GRAYLOG_HOST'), int(os.environ.get('GRAYLOG_PORT')))
    logger.addHandler(graypy_handler)

# getLogger('sqlalchemy.engine').setLevel(INFO)