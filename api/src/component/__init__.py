from collections import namedtuple
from .migrate import migrate
from .logging import logger

ComponentConfig = namedtuple("ComponentConfig", "module,url,name,legacy_table")
