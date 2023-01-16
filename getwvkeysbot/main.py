from http.client import HTTPException
from typing import Union

import discord
from discord.ext import commands

from getwvkeysbot.config import ADMIN_ROLES, ADMIN_USERS, BOT_PREFIX, BOT_TOKEN, GUILD_ID, IS_DEVELOPMENT, LOG_CHANNEL_ID, RABBIT_URI, VERIFIED_ROLE
from getwvkeysbot.util.rabbit import RpcClient
from getwvkeysbot.utils import FlagAction, OPCode, UserFlags, logger

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)
if not RABBIT_URI:
    logger.warn("RabbitMQ is not configured. Some features will not work.")
else:
    rpc_client = RpcClient("rpc_bot_queue_development", bot)


@bot.event
async def on_ready():
    # if IS_DEVELOPMENT:
    #     logger.info("Development mode is enabled, syncing commands to dev server...")
    #     bot.tree.copy_global_to(guild=discord.Object(id=DEVELOPMENT_GUILD))
    #     await bot.tree.sync(guild=discord.Object(id=DEVELOPMENT_GUILD)))
    logger.info("[Discord] Logged in as {}#{}".format(bot.user.name, bot.user.discriminator))


# handles banning of users
@bot.event
async def on_member_ban(guild: discord.Guild, user: Union[discord.User, discord.Member]):
    # ignore bots, unverified users, and guilds that aren't the main server
    if user.bot or not VERIFIED_ROLE in user._roles or not guild.id == GUILD_ID:
        return

    logger.info("[Discord] User {}#{} (`{}`) was banned from {}".format(user.name, user.discriminator, user.id, guild.name))

    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            await rpc_client.publish_packet(OPCode.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to disable user {}".format(user.id), e)
            return await log_channel.send("An error occurred while trying to disable user {}:{} (`{}`) from the database.".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was banned, their account has been disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.exception("[Discord]", e)


# handles kicking and leaving of users
@bot.event
async def on_member_remove(user: Union[discord.User, discord.Member]):
    # ignore bots, unverified users, and guilds that aren't the main server
    if user.bot or not VERIFIED_ROLE in user._roles or not user.guild.id == GUILD_ID:
        return

    logger.info("[Discord] User {}#{} (`{}`) was removed from {}".format(user.name, user.discriminator, user.id, user.guild.name))

    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            await rpc_client.publish_packet(OPCode.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to disable user {}".format(user.id), e)
            return await log_channel.send("An error occurred while trying to disable user {}:{} (`{}`).".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was removed, their account has been disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.exception("[Discord]", e)


# handles role changes of users
@bot.event
async def on_member_update(old: discord.Member, new: discord.Member):
    # ignore bots, changes that dont invole roles, and guilds that aren't the main server
    if old.bot or old.roles == new.roles or not old.guild.id == GUILD_ID:
        return

    # checks if the verified role was removed from a user
    if VERIFIED_ROLE not in new._roles:
        try:
            await rpc_client.publish_packet(OPCode.DISABLE_USER, {"user_id": new.id})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to disable user {}".format(new.id), e)
            return await new.guild.get_channel(LOG_CHANNEL_ID).send("An error occurred while trying to disable user {}:{} (`{}`).".format(new.name, new.discriminator, new.id))
        await new.guild.get_channel(LOG_CHANNEL_ID).send("User {}#{} (`{}`) was unverified, their account has been disabled.".format(new.name, new.discriminator, new.id))

    # checks uf the verified role was given to a user
    if VERIFIED_ROLE in new._roles:
        try:
            await rpc_client.publish_packet(OPCode.ENABLE_USER, {"user_id": new.id})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to enable user {}: {}".format(new.id), e)
            return await new.guild.get_channel(LOG_CHANNEL_ID).send("An error occurred while trying to enable user {}:{} (`{}`).".format(new.name, new.discriminator, new.id))
        await new.guild.get_channel(LOG_CHANNEL_ID).send("User {}#{} (`{}`) was verified, their account has been enabled.".format(new.name, new.discriminator, new.id))


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
        logger.exception("[Discord]", e)
        await ctx.reply("An error occurred while executing the command. Please try again later.")
        return
    if isinstance(e, commands.CommandError):
        logger.exception("[Discord]", e)
        await ctx.reply("An error occurred while executing the command. Please try again later.")
        return
    logger.exception("[Discord] An error occurred while executing the command {}".format(ctx.command.name), e)


@bot.command(help="Syncs commands", hidden=True)
@commands.is_owner()
async def synccommands(ctx: commands.Context):
    await bot.tree.sync()
    await ctx.reply("Synced commands.")


@bot.hybrid_command(help="Pong!")
async def ping(ctx: commands.Context):
    await ctx.reply(f"Pong! {round(bot.latency * 1000)}ms")


@bot.hybrid_command(hidden=True, help="Sync the guild bans with the database. This will disable users that are banned from the guild.")
@commands.cooldown(1, 3600, commands.BucketType.guild)
async def sync(ctx: commands.Context):
    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")
    m = await ctx.reply("Syncing the banned users with the database might take a while. Please be patient.")
    # sync the banned users with the database
    try:
        banned_users = [entry async for entry in ctx.guild.bans()]
        await rpc_client.publish_packet(OPCode.DISABLE_USER_BULK, {"user_ids": [ban.user.id for ban in banned_users]})
        await m.reply("{} guild bans have been synced with the database.".format(len(banned_users)))
    except Exception as e:
        logger.exception(e)
        await m.reply(content="An error occurred while syncing the guild bans: {}".format(e))


@bot.hybrid_command(name="usercount", help="Get the number of users that have registered on the site.")
async def user_count(ctx: commands.Context):
    try:
        await ctx.defer()
        count = await rpc_client.publish_packet(OPCode.USER_COUNT)
        await ctx.reply("There are currently {} users in the database.".format(count))
    except Exception as e:
        logger.exception(e)
        await ctx.reply("An error occurred while fetching the user count: {}".format(e))


@bot.hybrid_command(name="keycount", help="Get the number of cached keys in the database.")
async def key_count(ctx: commands.Context):
    try:
        count = await rpc_client.publish_packet(OPCode.KEY_COUNT)
        await ctx.reply("There are currently {} keys in the database.".format(count))
    except Exception as e:
        logger.exception(e)
        await ctx.reply("An error occurred while fetching the key count: {}".format(e))


@bot.hybrid_command(name="search", usage="<kid or pssh>", help="Search for a key by kid or pssh.")
async def key_search(ctx: commands.Context, query: str):
    if len(query) < 32:
        return await ctx.reply("Sorry, your query is not valid.")
    m = await ctx.reply(content="Searching...")
    try:
        results = await rpc_client.publish_packet(OPCode.SEARCH, {"query": query})
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
        logger.exception(e)
        await m.edit(content="An error occurred while searching: {}".format(e))


@bot.hybrid_command(hidden=True, help="Disable a user account")
async def disable_user(ctx: commands.Context, user: discord.User):
    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")
    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            await rpc_client.publish_packet(OPCode.DISABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to disable user {}".format(user.id), e)
            return await ctx.reply("An error occurred while trying to disable user {}:{} (`{}`)".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was disabled by {}#{} (`{}`)".format(user.name, user.discriminator, user.id, ctx.author.name, ctx.author.discriminator, ctx.author.id))
        await ctx.reply("User {}#{} (`{}`) was disabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.exception("[Discord]", e)
        await ctx.reply("An error occurred while disabling user: {}".format(e))


@bot.hybrid_command(hidden=True, help="Enable a user account")
async def enable_user(ctx: commands.Context, user: discord.User):
    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")
    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            await rpc_client.publish_packet(OPCode.ENABLE_USER, {"user_id": user.id})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to enable user {}".format(user.id), e)
            return await ctx.reply.send("An error occurred while trying to enable user {}:{} (`{}`)".format(user.name, user.discriminator, user.id))
        await log_channel.send("User {}#{} (`{}`) was enabled by {}#{} (`{}`)".format(user.name, user.discriminator, user.id, ctx.author.name, ctx.author.discriminator, ctx.author.id))
        await ctx.reply("User {}#{} (`{}`) was enabled.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.exception("[Discord]", e)
        await ctx.reply("An error occurred while enabling user: {}".format(e))


@bot.hybrid_command(hidden=True, help="Reset a users API Key")
# TODO: limit this to 2 times per day
async def reset_api_key(ctx: commands.Context, user: discord.User):
    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")
    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            await rpc_client.publish_packet(OPCode.RESET_API_KEY, {"user_id": user.id})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to reset API Key for {}".format(user.id), e)
            return await ctx.reply.send("An error occurred while trying to reset API Key for {}:{} (`{}`)".format(user.name, user.discriminator, user.id))
        await log_channel.send("API Key for {}#{} (`{}`) was reset by {}#{} (`{}`)".format(user.name, user.discriminator, user.id, ctx.author.name, ctx.author.discriminator, ctx.author.id))
        await ctx.reply("API Key for {}#{} (`{}`) was reset.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.exception("[Discord]", e)
        await ctx.reply("An error occurred while resetting user API Key: {}".format(e))


@bot.hybrid_command(hidden=True, help="Lists user flags", name="flags")
async def list_flags(ctx: commands.Context):
    names = []
    for name in UserFlags._member_names_:
        names.append(f"``{name}``")

    await ctx.reply(f"Valid user flags:\n{', '.join(names)}")


@bot.hybrid_command(hidden=True, help="Update a users flags")
async def update_flags(ctx: commands.Context, user: discord.User, action: str, flag: str):
    flag = flag.upper()
    action = action.upper()

    # only allow admins to use command
    if not ctx.author.id in ADMIN_USERS and not any(x.id in ADMIN_ROLES for x in ctx.author.roles):
        return await ctx.reply("You're not elite enough, try harder.")

    if action not in FlagAction._member_names_:
        return await ctx.reply("Invalid action! Valid actions are ``add``, ``remove``")

    if flag not in UserFlags._member_names_:
        names = []
        for name in UserFlags._member_names_:
            names.append(f"``{name}``")
        return await ctx.reply(f"Invalid User Flag! Valid flags are {', '.join(names)}")

    flag_value = UserFlags[flag].value
    action_value = FlagAction[action].value

    try:
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        try:
            await rpc_client.publish_packet(OPCode.UPDATE_PERMISSIONS, {"user_id": user.id, "permission_action": action_value, "permissions": flag_value})
        except HTTPException as e:
            logger.exception("[Discord] HTTPException while trying to update user permissions for {}".format(user.id), e)
            return await ctx.reply.send("An error occurred while trying to update permissions for {}:{} (`{}`)".format(user.name, user.discriminator, user.id))
        await log_channel.send(
            "Permissions for {}#{} (`{}`) were updated by {}#{} (`{}`). {} {}".format(
                user.name, user.discriminator, user.id, ctx.author.name, ctx.author.discriminator, ctx.author.id, action_value, flag_value
            )
        )
        await ctx.reply("Permissions for {}#{} (`{}`) were updated.".format(user.name, user.discriminator, user.id))
    except Exception as e:
        logger.exception("[Discord]", e)
        await ctx.reply("An error occurred while updating user permissions: {}".format(e))


def main():
    if IS_DEVELOPMENT:
        logger.warning("RUNNING IN DEVELOPMENT MODE")
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
