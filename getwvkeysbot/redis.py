import json
import logging
import random
from enum import Enum

import discord

import redis
from getwvkeysbot.config import GUILD_ID, INTERROGATION_ROOM_CHANNEL_ID, MODERATOR_ROLE, QUARANTINE_LOG_CHANNEL_ID, REDIS_URI, SUS_ROLE, VERIFIED_ROLE
from getwvkeysbot.shared import bot

logger = logging.getLogger(__name__)


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


redis_cli = redis.Redis.from_url(REDIS_URI, decode_responses=True, encoding="utf8")
p = redis_cli.pubsub(ignore_subscribe_messages=True)


async def quarantine(d):
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
        return print("failed to get member, probably left")
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
    await thread.send(embed=embed2, allowed_mentions=discord.AllowedMentions(roles=True), content=f"<@&{MODERATOR_ROLE}> {member.mention}")


def redis_message_handler(msg):
    try:
        data = json.loads(msg.get("data"))
        op = data.get("op")
        d = data.get("d")

        if op == OPCode.QUARANTINE.value:
            bot.loop.create_task(quarantine(d))
        else:
            logger.warn("Unknown opcode: {}".format(op))

    except json.JSONDecodeError as e:
        logger.exception("Error parsing json", e)


p.subscribe(**{"bot": redis_message_handler})
redis_thread = p.run_in_thread(daemon=True)


def make_api_request(action: OPCode, data={}):
    reply_address = "api-" + str(random.randint(1000, 9999))
    p.subscribe(reply_address)
    payload = {"op": action.value, "d": data, "reply_to": reply_address}

    redis_cli.publish("api", json.dumps(payload))
    for message in p.listen():
        logger.debug(message)
        if message["type"] == "message":
            p.unsubscribe(reply_address)
            rd = json.loads(message["data"])
            rmsg = rd["d"]["message"]
            rop = rd["op"]
            if rop == OPCode.ERROR.value:
                raise Exception(rmsg)
            return rmsg
