import base64
from enum import Enum
import json
import logging
import logging.handlers
from coloredlogs import ColoredFormatter
import requests

from config import API_URL, CLIENT_ID, CLIENT_SECRET, LOG_DATE_FORMAT, LOG_FILE_PATH, LOG_FORMAT, LOG_LEVEL

logger = logging.getLogger(__name__)


class APIAction(Enum):
    DISABLE_USER = "disable"
    DISABLE_USER_BULK = "disable_bulk"
    ENABLE_USER = "enable"
    KEY_COUNT = "keycount"
    USER_COUNT = "usercount"
    SEARCH = "search"


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


def make_api_request(action: APIAction, data={}):
    data["action"] = action.value
    header = {"X-API-Key": base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET).encode()).decode("utf8")}
    logger.debug("Making request to {} with data {} and header {}".format(API_URL, json.dumps(data), json.dumps(header)))
    res = requests.post(API_URL, json=data, headers=header)
    # res.raise_for_status()
    if not res.ok and len(res.content) == 0:
        res.raise_for_status()
    d = res.json()
    logger.debug("Recieved response from {}: {}".format(API_URL, json.dumps(d)))
    if d.get("error", False) == True:
        raise Exception("API Error: Recieved HTTP Code {} with message: {}".format(d.get("code"), d.get("message")))

    return d.get("message")
