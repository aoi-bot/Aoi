import discord
from discord.ext import commands
import aoi


class Weather(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Look up weather data for a location"


    @commands.command(
        brief="Look up a current satellite image"
    )
    async def satellite(self, lat: float, long: float):
        raise NotImplemented



def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Weather(bot))
