import discord
from discord.ext import commands
import aoi


class Nasa(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "A collection of commands to look up data from NASA"



def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Nasa(bot))
