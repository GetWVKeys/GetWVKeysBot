import logging
import logging.handlers
from enum import Enum

from coloredlogs import ColoredFormatter

from getwvkeysbot.config import LOG_DATE_FORMAT, LOG_FILE_PATH, LOG_FORMAT, LOG_LEVEL

logger = logging.getLogger(__name__)


class UserFlags(Enum):
    ADMIN = 1 << 0
    BETA_TESTER = 1 << 1
    VINETRIMMER = 1 << 2
    KEY_ADDING = 1 << 3
    SUSPENDED = 1 << 4
    BLACKLIST_EXEMPT = 1 << 5


class FlagAction(Enum):
    ADD = "add"
    REMOVE = "remove"


def construct_logger():
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # setup handlers
    # create a colored formatter for the console
    console_formatter = ColoredFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    # create a regular non-colored formatter for the log file
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    # create a handler for console logging
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(console_formatter)
    # create a handler for file logging, 5 mb max size, with 5 backup files
    file_handler = logging.handlers.RotatingFileHandler(LOG_FILE_PATH, maxBytes=(1024 * 1024) * 5, backupCount=5)
    file_handler.setFormatter(file_formatter)

    # construct the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(stream)
    logger.addHandler(file_handler)
    return logger
