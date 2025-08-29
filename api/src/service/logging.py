import logging
import sys
from logging import INFO, basicConfig, getLogger


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s %(name)s:T%(process)d (%(filename)s:%(lineno)d) %(levelname)s: %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s:T%(process)d: %(message)s",
    stream=sys.stderr,
    level=INFO,
)
for handler in logging.root.handlers:
    handler.setFormatter(CustomFormatter())

logger = getLogger("makeradmin")

# getLogger('sqlalchemy.engine').setLevel(INFO)
