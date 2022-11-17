import logging
import os
import pathlib
import time

from dotenv import load_dotenv

IS_DEVELOPMENT = os.environ.get("DEVELOPMENT", False)
IS_STAGING = os.environ.get("STAGING", False)

load_dotenv(".env.dev" if IS_DEVELOPMENT else ".env")

# Logging settings
LOG_LEVEL = logging.DEBUG if IS_DEVELOPMENT else logging.INFO
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(funcName)s:%(lineno)d] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%I:%M:%S"
LOG_FILE_PATH = pathlib.Path(os.getcwd(), "logs", f"{time.strftime('%Y-%m-%d')}.log")

# Channels and roles
LOG_CHANNEL_ID = int(os.environ["LOG_CHANNEL_ID"])
ADMIN_USERS = [int(x) for x in os.environ["ADMIN_USERS"].split(",")]
VERIFIED_ROLE = int(os.environ["VERIFIED_ROLE"])
SUS_ROLE = int(os.environ["SUS_ROLE"])
ADMIN_ROLES = [int(x) for x in os.environ["ADMIN_ROLES"].split(",")]
QUARANTINE_LOG_CHANNEL_ID = int(os.environ["QUARANTINE_LOG_CHANNEL_ID"])
INTERROGATION_ROOM_CHANNEL_ID = int(os.environ["INTERROGATION_ROOM_CHANNEL_ID"])
MODERATOR_ROLE = int(os.environ["MODERATOR_ROLE"])
GUILD_ID = int(os.environ["GUILD_ID"])


# Environment settings
BOT_PREFIX = os.environ["PREFIX"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
RABBIT_URI = os.environ["RABBIT_URI"]
