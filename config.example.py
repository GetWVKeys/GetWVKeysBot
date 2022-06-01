from enum import Enum
import logging
import os
import pathlib
import time


# DO NOT CHANGE THIS
class APIAction(Enum):
    DISABLE_USER = "disable",
    ENABLE_USER = "enable",
    KEY_COUNT = "keycount",
    USER_COUNT = "usercount"


IS_DEVELOPMENT = os.environ.get("DEVELOPMENT", False)
LOG_LEVEL = logging.DEBUG if IS_DEVELOPMENT else logging.INFO
LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(funcName)s:%(lineno)d] %(levelname)s: %(message)s'
LOG_DATE_FORMAT = '%I:%M:%S'
LOG_FILE_PATH = pathlib.Path(
    os.getcwd(), "logs", f"{time.strftime('%Y-%m-%d')}.log")

LOG_CHANNEL_ID = "channel id where logs should go"
BOT_PREFIX = "wvd!" if IS_DEVELOPMENT else "wv!"
ADMIN_USERS = ["list", "of", "discord", "user", "ids"]
API_URL = "local api url" if IS_DEVELOPMENT else "remote api url"
BOT_TOKEN = "development bot token" if IS_DEVELOPMENT else "production bot token"
CLIENT_ID = "bot id"
CLIENT_SECRET = "oauth2 secret"
