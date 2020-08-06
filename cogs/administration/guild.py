import discord
from discord.ext import commands
import aoi


class Guilds(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.has_permissions(manage_guild=True)
    @commands.command()
    async def renameguild(self, ctx: aoi.AoiContext, *, name: str):
        await ctx.confirm_coro(f"Rename server to `{name}`?",
                               f"Server renamed to `{name}`",
                               "Server rename cancelled",
                               ctx.guild.edit(name=name))


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Guilds(bot))
