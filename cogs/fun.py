from discord.ext import commands

import aoi


class Fun(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self) -> str:
        return "Fun! :D"
    

def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Fun(bot))
