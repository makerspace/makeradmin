import logging
import logging.handlers
import os
import sys
from datetime import datetime
from logging import INFO, basicConfig, getLogger
from typing import Any

from .config import config


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s %(name)10s:T%(process)d (%(filename)s:%(lineno)d) %(levelname)s: %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }

    def format(self, record: Any) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


basicConfig(
    # format="%(asctime)s %(levelname)s:%(name)s:T%(process)d: %(message)s",
    stream=sys.stderr,
    level=INFO,
)
for handler in logging.root.handlers:
    handler.setFormatter(CustomFormatter())

logs_dir = config.get("LOG_DIR")
if logs_dir:
    # Parent dir because the docker container runs with 'src' as the work directory
    log_dir = os.path.join("..", logs_dir)
    if not os.path.isdir(log_dir):
        print(f"Expected logs directory ({os.path.abspath(log_dir)}) to exist")
        exit(1)

    log_filename = datetime.now().strftime("service.log")
    log_path = os.path.abspath(os.path.join(log_dir, log_filename))

    file_handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s:T%(process)d (%(filename)s:%(lineno)d) %(levelname)s: %(message)s")
    )
    logging.root.addHandler(file_handler)

logger = getLogger("makeradmin")
