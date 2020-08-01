import discord
from discord.ext import commands

import aoi
from utils import conversions


class GuildSettings(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.has_guild_permissions(manage_guild=True)
    @commands.command(
        aliases=["okclr"],
        brief="Sets the OK embed color"
    )
    async def okcolor(self, ctx: aoi.AoiContext, color: discord.Color):
        await self.bot.db.set_ok_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    @commands.has_guild_permissions(manage_guild=True)
    @commands.command(
        aliases=["infoclr"],
        brief="Sets the Info embed color"
    )
    async def infocolor(self, ctx: aoi.AoiContext, color: discord.Color):
        await self.bot.db.set_info_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    @commands.has_guild_permissions(manage_guild=True)
    @commands.command(
        aliases=["errorclr"],
        brief="Sets the Error embed color"
    )
    async def errorcolor(self, ctx: aoi.AoiContext, color: discord.Color):
        await self.bot.db.set_error_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(GuildSettings(bot))
