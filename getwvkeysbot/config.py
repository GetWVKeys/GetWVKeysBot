import os
import pathlib
import time

import toml

IS_DEVELOPMENT = os.environ.get("DEVELOPMENT", False)
IS_STAGING = os.environ.get("STAGING", False)
config_filename = "config.dev.toml" if IS_DEVELOPMENT else "config.staging.toml" if IS_STAGING else "config.toml"
config = toml.load(config_filename)

general = config["general"]
channels = general["channels"]
roles = general["roles"]
rabbitmq = config["rabbitmq"]
discord = config["discord"]
logging_config = config["logging"]

# General Configuration Section
BOT_PREFIX: str = general["prefix"]
ADMIN_USERS: list[int] = general["admin_users"]
GUILD_ID: int = general["guild_id"]

# Channel Configuration Section
LOG_CHANNEL_ID: int = channels["logs"]
QUARANTINE_LOG_CHANNEL_ID: int = channels["quarantine_logs"]
INTERROGATION_ROOM_CHANNEL_ID: int = channels["interrogation_room"]

# Role Configuration Section
VERIFIED_ROLE: int = roles["verified"]
SUS_ROLE: int = roles["sus"]
MODERATOR_ROLE: int = roles["moderator"]
ADMIN_ROLES: list[int] = roles["admin"]

# Discord Configuration Section
CLIENT_ID: str = discord["client_id"]
CLIENT_SECRET: str = discord["client_secret"]
BOT_TOKEN: str = discord["token"]

# RabbitMQ Configuration Section
RABBIT_URI: str = rabbitmq["uri"]


# Logging Configuration Section
CONSOLE_LOG_LEVEL: str = logging_config["console_level"]
FILE_LOG_LEVEL: str = logging_config["file_level"]
LOG_FORMAT: str = logging_config["format"]
LOG_DATE_FORMAT: str = logging_config["date_format"]
LOG_FILE_PATH: pathlib.Path = pathlib.Path(os.getcwd(), logging_config["filename_format"].replace("%time%", time.strftime("%Y-%m-%d")))
