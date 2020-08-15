import discord
from discord.ext import commands
import aoi


class Weather(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Look up weather data for a location"


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Weather(bot))
