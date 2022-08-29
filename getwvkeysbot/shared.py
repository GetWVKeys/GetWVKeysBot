import discord
from discord.ext import commands

from getwvkeysbot.config import BOT_PREFIX

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)
