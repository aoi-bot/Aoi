import logging
import os

import discord
from discord.ext import commands
import dotenv

import aoi

logging.basicConfig(level=logging.INFO)
dotenv.load_dotenv(".env")

bot = aoi.AoiBot(command_prefix=commands.when_mentioned_or(","))

extensions = [
    "cogs.administration.aoi"
]

for ext in extensions:
    bot.load_extension(ext)

@bot.event
async def on_ready():
    logging.info("Bot online!")
    await bot.change_presence(activity=discord.Game("Hello :)"))

bot.run(os.getenv("TOKEN"))
