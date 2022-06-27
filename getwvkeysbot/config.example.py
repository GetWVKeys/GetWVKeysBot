from enum import Enum
import logging
import os
import pathlib
import time


# DO NOT CHANGE THIS
class APIAction(Enum):
    DISABLE_USER = "disable"
    ENABLE_USER = "enable"
    KEY_COUNT = "keycount"
    USER_COUNT = "usercount"


IS_DEVELOPMENT = os.environ.get("DEVELOPMENT", False)
LOG_LEVEL = logging.DEBUG if IS_DEVELOPMENT else logging.INFO
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(funcName)s:%(lineno)d] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%I:%M:%S"
LOG_FILE_PATH = pathlib.Path(os.getcwd(), "logs", f"{time.strftime('%Y-%m-%d')}.log")

LOG_CHANNEL_ID = 971335086609936384
BOT_PREFIX = "wvd!" if IS_DEVELOPMENT else "wv!"
ADMIN_USERS = [213247101314924545, 756153425682497536]
VERIFIED_ROLE = 970332150891155607
SUS_ROLE = 981080014722301952
ADMIN_ROLES = [975780356970123265, 979052545957842954]
BOT_TOKEN = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" if IS_DEVELOPMENT else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
CLIENT_ID = "981289795416379464"
CLIENT_SECRET = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
API_URL = "local api url" if IS_DEVELOPMENT else "remote api url"
