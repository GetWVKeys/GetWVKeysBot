import logging
import logging.handlers
from enum import Enum

import discord
from coloredlogs import ColoredFormatter

from getwvkeysbot.config import (
    CONSOLE_LOG_LEVEL,
    FILE_LOG_LEVEL,
    GUILD_ID,
    INTERROGATION_ROOM_CHANNEL_ID,
    LOG_DATE_FORMAT,
    LOG_FILE_PATH,
    LOG_FORMAT,
    MODERATOR_ROLE,
    QUARANTINE_LOG_CHANNEL_ID,
    SUS_ROLE,
    VERIFIED_ROLE,
)

LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
# setup handlers
# create a colored formatter for the console
console_formatter = ColoredFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
# create a regular non-colored formatter for the log file
file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
# create a handler for console logging
stream = logging.StreamHandler()
stream.setLevel(CONSOLE_LOG_LEVEL)
stream.setFormatter(console_formatter)
# create a handler for file logging, 5 mb max size, with 5 backup files
file_handler = logging.handlers.RotatingFileHandler(LOG_FILE_PATH, maxBytes=(1024 * 1024) * 5, backupCount=5)
file_handler.setFormatter(file_formatter)

# construct the logger
logger = logging.getLogger(__name__)
logger.setLevel(FILE_LOG_LEVEL)
logger.addHandler(stream)
logger.addHandler(file_handler)


class OPCode(Enum):
    ERROR = -1
    DISABLE_USER = 0
    DISABLE_USER_BULK = 1
    ENABLE_USER = 2
    KEY_COUNT = 3
    USER_COUNT = 4
    SEARCH = 5
    UPDATE_PERMISSIONS = 6
    QUARANTINE = 7
    REPLY = 8
    RESET_API_KEY = 9


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


async def quarantine(bot: discord.Client, d: dict):
    user_id = d["user_id"]
    url = d["url"]
    buildinfo = d["buildinfo"]
    pssh = d["pssh"]
    reason = d["reason"]

    await bot.wait_until_ready()
    log_channel = await bot.fetch_channel(QUARANTINE_LOG_CHANNEL_ID)
    thread_channel = await bot.fetch_channel(INTERROGATION_ROOM_CHANNEL_ID)
    guild = bot.get_guild(GUILD_ID)
    member = guild.get_member(int(user_id))

    if not member:
        logger.error("[Auto Quarantine] Failed to get member, probably left")
        return
    await member.add_roles(discord.utils.get(member.guild.roles, id=SUS_ROLE), reason="Auto Quarantine")
    await member.remove_roles(discord.utils.get(member.guild.roles, id=VERIFIED_ROLE), reason="Auto Quarantine")

    embed = discord.Embed(title="⚠️ User Quarantined", color=discord.Color.red(), description="A User has been automatically quarantined.")
    embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=False)
    embed.add_field(name="URL", value=url, inline=False)
    embed.add_field(name="BuildInfo", value=buildinfo, inline=False)
    embed.add_field(name="PSSH", value=pssh, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    await log_channel.send(embed=embed)

    thread = await thread_channel.create_thread(name=f"quarantine-{user_id}", type=discord.ChannelType.private_thread, reason="Auto Quarantine", invitable=False)
    embed2 = discord.Embed(title="⚠️ User Quarantined", color=discord.Color.red(), description="You have been automatically quarantined. Your account has been disabled and staff have been notified.")
    embed2.add_field(name="Reason", value=reason, inline=False)
    await thread.send(embed=embed2, allowed_mentions=discord.AllowedMentions(roles=True, users=True), content=f"<@&{MODERATOR_ROLE}> {member.mention}")
