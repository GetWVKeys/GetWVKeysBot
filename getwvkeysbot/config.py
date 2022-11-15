import logging
import os
import pathlib
import time

from dotenv import load_dotenv

IS_DEVELOPMENT = os.environ.get("DEVELOPMENT", False)

load_dotenv(".env.dev" if IS_DEVELOPMENT else ".env")

# Logging settings
LOG_LEVEL = logging.DEBUG if IS_DEVELOPMENT else logging.INFO
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(funcName)s:%(lineno)d] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%I:%M:%S"
LOG_FILE_PATH = pathlib.Path(os.getcwd(), "logs", f"{time.strftime('%Y-%m-%d')}.log")

# Channels and roles
LOG_CHANNEL_ID = 971335086609936384
ADMIN_USERS = [213247101314924545, 756153425682497536]
VERIFIED_ROLE = 970332150891155607
SUS_ROLE = 981080014722301952
ADMIN_ROLES = [994099299082309682, 979052545957842954]
DEVELOPMENT_GUILD = 820832976304472085

# Environment settings
BOT_PREFIX = os.environ["PREFIX"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REDIS_URI = os.environ["REDIS_URI"]
