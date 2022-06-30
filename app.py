from http.client import HTTPException
from typing import Union
import discord
from discord.ext import commands
from config import ADMIN_ROLES, ADMIN_USERS, BOT_PREFIX, BOT_TOKEN, IS_DEVELOPMENT, LOG_CHANNEL_ID, SUS_ROLE, VERIFIED_ROLE
from utils import construct_logger, make_api_request, APIAction


logger = construct_logger()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


@bot.event
async def on_ready():
    logger.info("[Discord] Logged in as {}#{}".format(bot.user.name, bot.user.discriminator))


@bot.event
async def on_member_ban(guild: discord.Guild, user: Union[discord.User, discord.Member]):
    # handles banning of users
    if user.bot:
        # ignore bots
        return
    logger.info("[Discord] User {}#{} (`{}`) was banned from {}".format(user.name, user.discriminator, user.id, guild.name))

    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            make_api_request(APIAction.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.error("[Discord] HTTPException while trying to disable user {}: {}".format(user.id, e))
            return await log_channel.send("An error occurred while trying to disable user {}:{} (`{}`) from the database. <@&975780356970123265>".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was banned, their account has been disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.error("[Discord] {}".format(e))


@bot.event
async def on_member_remove(guild: discord.Guild, user: Union[discord.User, discord.Member]):
    # handles kicking and leaving of users
    if user.bot:
        # ignore bots
        return
    logger.info("[Discord] User {}#{} (`{}`) was removed from {}".format(user.name, user.discriminator, user.id, guild.name))

    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            make_api_request(APIAction.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.error("[Discord] HTTPException while trying to disable user {}: {}".format(user.id, e))
            return await log_channel.send("An error occurred while trying to disable user {}:{} (`{}`). <@&975780356970123265>".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was removed, their account has been disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.error("[Discord] {}".format(e))


@bot.event
async def on_member_update(old: discord.Member, new: discord.Member):
    # handles role changes of users
    if old.bot:
        return
    if old.roles == new.roles:
        return

    if VERIFIED_ROLE not in new._roles:
        # for when a user is unverified
        try:
            make_api_request(APIAction.DISABLE_USER, {"user_id": new.id})
        except HTTPException as e:
            logger.error("[Discord] HTTPException while trying to disable user {}: {}".format(new.id, e))
            return await new.guild.get_channel(LOG_CHANNEL_ID).send("An error occurred while trying to disable user {}:{} (`{}`). <@&975780356970123265>".format(new.name, new.discriminator, new.id))
        await new.guild.get_channel(LOG_CHANNEL_ID).send("User {}#{} (`{}`) was unverified, their account has been disabled.".format(new.name, new.discriminator, new.id))
        return
    elif VERIFIED_ROLE in new._roles and SUS_ROLE in old._roles:
        # for when a user is no longer sus
        try:
            make_api_request(APIAction.ENABLE_USER, {"user_id": new.id})
        except HTTPException as e:
            logger.error("[Discord] HTTPException while trying to enable user {}: {}".format(new.id, e))
            return await new.guild.get_channel(LOG_CHANNEL_ID).send("An error occurred while trying to enable user {}:{} (`{}`). <@&975780356970123265>".format(new.name, new.discriminator, new.id))
        await new.guild.get_channel(LOG_CHANNEL_ID).send("User {}#{} (`{}`) was verified, their account has been enabled.".format(new.name, new.discriminator, new.id))
        return


@bot.event
async def on_command_error(ctx: commands.Context, e: Exception):
    if isinstance(e, commands.CommandNotFound):
        return
    if isinstance(e, commands.MissingRequiredArgument):
        await ctx.reply("You are missing a required argument. Please check the command's syntax.")
        return
    if isinstance(e, commands.BadArgument):
        await ctx.reply("Please check the argument you provided. It is invalid.")
        return
    if isinstance(e, commands.CheckFailure):
        await ctx.reply("You are not allowed to use this command.")
        return
    if isinstance(e, commands.CommandOnCooldown):
        await ctx.reply("You are on cooldown. Please wait {} seconds before using this command again.".format(round(e.retry_after)))
        return
    if isinstance(e, commands.CommandInvokeError):
        logger.error("[Discord] {}".format(e))
        await ctx.reply("An error occurred while executing the command. Please try again later.")
        return
    if isinstance(e, commands.CommandError):
        logger.error("[Discord] {}".format(e))
        await ctx.reply("An error occurred while executing the command. Please try again later.")
        return
    logger.error("[Discord] An error occurred while executing the command {}".format(ctx.command.name))
    logger.error("[Discord] {}".format(e))


@bot.command(help="Pong!")
async def ping(ctx):
    await ctx.reply(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command(hidden=True, help="Sync the guild bans with the database. This will disable users that are banned from the guild.")
@commands.cooldown(1, 3600, commands.BucketType.guild)
async def sync(ctx: commands.Context):
    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")
    m = await ctx.send("Syncing the banned users with the database might take a while. Please be patient.")
    # sync the banned users with the database
    try:
        banned_users = [entry async for entry in ctx.guild.bans()]
        make_api_request(APIAction.DISABLE_USER_BULK, {"user_ids": [ban.user.id for ban in banned_users]})
        await m.reply("{} guild bans have been synced with the database.".format(len(banned_users)))
    except Exception as e:
        logger.error(e)
        await m.reply(content="An error occurred while syncing the guild bans.")


@bot.command(name="usercount", help="Get the number of users that have registered on the site.")
async def user_count(ctx):
    try:
        count = make_api_request(APIAction.USER_COUNT)
        await ctx.reply("There are currently {} users in the database.".format(count))
    except Exception as e:
        logger.error(e)
        await ctx.reply("An error occurred while fetching the user count.")


@bot.command(name="keycount", help="Get the number of cached keys in the database.")
async def key_count(ctx):
    try:
        count = make_api_request(APIAction.KEY_COUNT)
        await ctx.reply("There are currently {} keys in the database.".format(count))
    except Exception as e:
        logger.error(e)
        await ctx.reply("An error occurred while fetching the key count.")


@bot.command(name="search", usage="<kid or pssh>", help="Search for a key by kid or pssh.")
async def key_search(ctx: commands.Context, query):
    if len(query) < 32:
        return await ctx.reply("Sorry, your query is not valid.")
    m = await ctx.send(content="Searching...")
    try:
        results = make_api_request(APIAction.SEARCH, {"query": query})
        if not results:
            return await m.edit(content="The response was null. Please report this to the developers.")
        kid = results.get("kid")
        keys = results.get("keys")
        if len(keys) == 0:
            return await m.edit(content="There were no results. sadface.")

        embed = discord.Embed(title="Search Results for '{}'".format(query), description="Found **{}** result{}".format(len(keys), "s" if len(keys) > 1 else ""))

        results_field = ""
        for key_entry in keys:
            key = key_entry.get("key")
            # added_at = key_entry.get("added_at")
            # license_url = key_entry.get("license_url")
            field_value = "{}\n".format(key)
            # if adding the field_value to results_field exceeds 1024 characters, don't add the field
            if len(results_field + field_value) > 1024:
                logger.warn("Adding the field value to the results field would exceed 1024 characters. KID: {}".format(kid))
                embed.set_footer(text="{} keys were omitted.".format(len(keys) - len(results_field.split("\n"))))
                break
            results_field += field_value

        embed.add_field(name="Results", value=results_field, inline=False)

        await m.edit(embed=embed, content="")
    except Exception as e:
        logger.error(e)
        await m.edit(content="An error occurred while searching.")


@bot.command(hidden=True, help="Disable a user account")
async def disable_user(ctx: commands.Context, user: discord.User):
    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")
    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            make_api_request(APIAction.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.error("[Discord] HTTPException while trying to disable user {}: {}".format(user.id, e))
            return await ctx.reply("An error occurred while trying to disable user {}:{} (`{}`) <@&975780356970123265>".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was disabled by {}#{} (`{}`)".format(user.name, user.discriminator, user.id, ctx.author.name, ctx.author.discriminator, ctx.author.id))
        await ctx.reply("User {}#{} (`{}`) was disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.error("[Discord] {}".format(e))
        await ctx.reply("An error occurred while disabling user.")


@bot.command(hidden=True, help="Enable a user account")
async def enable_user(ctx: commands.Context, user: discord.User):
    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")
    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            make_api_request(APIAction.ENABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.error("[Discord] HTTPException while trying to enable user {}: {}".format(user.id, e))
            return await ctx.reply.send("An error occurred while trying to enable user {}:{} (`{}`) <@&975780356970123265>".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was enable by {}#{} (`{}`)".format(user.name, user.discriminator, user.id, ctx.author.name, ctx.author.discriminator, ctx.author.id))
        await ctx.reply("User {}#{} (`{}`) was enabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.error("[Discord] {}".format(e))
        await ctx.reply("An error occurred while enabling user.")


if __name__ == "__main__":
    if IS_DEVELOPMENT:
        logger.warning("RUNNING IN DEVELOPMENT MODE")
    bot.run(BOT_TOKEN)
