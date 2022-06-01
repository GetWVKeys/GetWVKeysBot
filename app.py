from http.client import HTTPException
from typing import Union
import discord
from discord.ext import commands
from config import ADMIN_USERS, BOT_PREFIX, BOT_TOKEN, IS_DEVELOPMENT, LOG_CHANNEL_ID
from utils import construct_logger, make_api_request, APIAction


logger = construct_logger()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


@bot.event
async def on_ready():
    logger.info("[Discord] Logged in as {}#{}".format(
        bot.user.name, bot.user.discriminator))


@bot.event
async def on_member_ban(guild: discord.Guild, user: Union[discord.User, discord.Member]):
    # ignore bots
    if user.bot:
        return
    logger.info("[Discord] User {}#{} (`{}`) was banned from {}".format(
        user.name, user.discriminator, user.id, guild.name))

    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            make_api_request(APIAction.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.error(
                "[Discord] HTTPException while trying to disable user {}: {}".format(user.id, e))
            return await log_channel.send("An error occurred while trying to disable user {}:{} (`{}`) from the database. <@&975780356970123265>".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was banned, their account has been disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.error("[Discord] {}".format(e))


@bot.event
async def on_member_remove(guild: discord.Guild, user: Union[discord.User, discord.Member]):
    # ignore bots
    if user.bot:
        return
    logger.info("[Discord] User {}#{} (`{}`) was removed from {}".format(
        user.name, user.discriminator, user.id, guild.name))

    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            make_api_request(APIAction.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.error(
                "[Discord] HTTPException while trying to disable user {}: {}".format(user.id, e))
            return await log_channel.send("An error occurred while trying to disable user {}:{} (`{}`) from the database. <@&975780356970123265>".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was removed, their account has been disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.error("[Discord] {}".format(e))


@bot.event
async def on_command_error(ctx: commands.Context, e: Exception):
    if isinstance(e, commands.CommandNotFound):
        return
    if isinstance(e, commands.MissingRequiredArgument):
        await ctx.send("You are missing a required argument. Please check the command's syntax.")
        return
    if isinstance(e, commands.BadArgument):
        await ctx.send("Please check the argument you provided. It is invalid.")
        return
    if isinstance(e, commands.CheckFailure):
        await ctx.send("You are not allowed to use this command.")
        return
    if isinstance(e, commands.CommandOnCooldown):
        await ctx.send("You are on cooldown. Please wait {} seconds before using this command again.".format(
            round(e.retry_after)))
        return
    if isinstance(e, commands.CommandInvokeError):
        logger.error("[Discord] {}".format(e))
        await ctx.send("An error occurred while executing the command. Please try again later.")
        return
    if isinstance(e, commands.CommandError):
        logger.error("[Discord] {}".format(e))
        await ctx.send("An error occurred while executing the command. Please try again later.")
        return
    logger.error("[Discord] An error occurred while executing the command {}".format(
        ctx.command.name))
    logger.error("[Discord] {}".format(e))


@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')


@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.guild)
async def sync(ctx: commands.Context):
    # only allow admins to use command
    if not str(ctx.author.id) in ADMIN_USERS:
        return await ctx.send("You're not elite enough, try harder.")
    m = await ctx.send("Syncing the banned users with the database might take a while. Please be patient.")
    # sync the banned users with the database
    try:
        banned_users = [entry async for entry in ctx.guild.bans()]
        make_api_request(APIAction.DISABLE_USER_BULK, {"user_ids": [
                         ban.user.id for ban in banned_users]})
        await m.reply("{} guild bans have been synced with the database.".format(len(banned_users)))
    except Exception as e:
        logger.error(e)
        await m.reply(content="An error occurred while syncing the guild bans.")


@bot.command(name="usercount")
async def user_count(ctx):
    try:
        count = make_api_request(APIAction.USER_COUNT)
        await ctx.send("There are currently {} users in the database.".format(count))
    except Exception as e:
        logger.error(e)
        await ctx.send("An error occurred while fetching the user count.")


@bot.command(name="keycount")
async def key_count(ctx):
    try:
        count = make_api_request(APIAction.KEY_COUNT)
        await ctx.send("There are currently {} users in the database.".format(count))
    except Exception as e:
        logger.error(e)
        await ctx.send("An error occurred while fetching the user count.")


@bot.command(name="search")
async def key_search(ctx, query):
    pass


if __name__ == "__main__":
    if IS_DEVELOPMENT:
        logger.warning("RUNNING IN DEVELOPMENT MODE")
    bot.run(BOT_TOKEN)
