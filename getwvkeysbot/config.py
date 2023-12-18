import logging
import os
import pathlib
import time

from dotenv import load_dotenv

IS_DEVELOPMENT = os.environ.get("DEVELOPMENT", False)

load_dotenv(".env.dev" if IS_DEVELOPMENT else ".env")

# Logging settings
LOG_LEVEL = logging.DEBUG if IS_DEVELOPMENT else logging.INFO
LOG_FORMAT = (
    "[%(asctime)s] [%(name)s] [%(funcName)s:%(lineno)d] %(levelname)s: %(message)s"
)
LOG_DATE_FORMAT = "%I:%M:%S"
LOG_FILE_PATH = pathlib.Path(os.getcwd(), "logs", f"{time.strftime('%Y-%m-%d')}.log")

# Channels and roles
LOG_CHANNEL_ID = 1186393779574407288
SCRIPTS_CHANNEL_ID = 1049388138000302173
ADMIN_USERS = [498989696412549120, 756153425682497536]
VERIFIED_ROLE = 1186393778500665348
SUS_ROLE = 981080014722301952
ADMIN_ROLES = [994099299082309682, 979052545957842954]
SCRIPT_DEV_ROLE_ID = 992838358378237983
DEVELOPMENT_GUILD = 1186393778500665344

# Environment settings
BOT_PREFIX = os.environ["PREFIX"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
