import logging
import os

import discord
import dotenv
from discord.ext import commands

import aoi
import asyncio

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv(".env")


def get_prefix(_bot: aoi.AoiBot, message: discord.Message):
    if message.guild.id not in _bot.db.prefixes:
        asyncio.create_task(_bot.db.guild_setting(message.guild.id))
        return commands.when_mentioned_or(",")(_bot, message)
    return commands.when_mentioned_or(_bot.db.prefixes[message.guild.id])(_bot, message)


bot = aoi.AoiBot(command_prefix=get_prefix)

extensions = [
    "cogs.administration.aoi",
    "cogs.administration.information",
    "cogs.administration.roles",
    "cogs.settings.guildsettings",
    "cogs.errorhandler"
]

for ext in extensions:
    bot.load_extension(ext)


@bot.event
async def on_ready():
    logging.info("Bot online!")
    await bot.change_presence(activity=discord.Game("Hello :)"))


bot.run(os.getenv("TOKEN"))
