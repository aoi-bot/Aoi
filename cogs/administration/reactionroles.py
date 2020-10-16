import discord
from discord.ext import commands
import aoi


class ReactionRoles(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands to manage reaction roles"


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(ReactionRoles(bot))
