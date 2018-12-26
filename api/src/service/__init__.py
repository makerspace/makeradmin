from collections import namedtuple
from .migrate import migrate
from .logging import logger

InternalServiceConfig = namedtuple("InternalServiceConfig", "name,path,module")


ExternalServiceConfig = namedtuple("ExternalServiceConfig", "name,path,url")
