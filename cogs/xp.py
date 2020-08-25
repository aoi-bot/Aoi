import discord
from discord.ext import commands

import aoi


# xp levelling functions

def _xp_per_level(lvl: int):
    return 8 * lvl + 40


def _level(xp: int):
    lvl = 0
    while xp > _xp_per_level(lvl):
        xp -= _xp_per_level(lvl)
        lvl += 1
    return lvl, xp


class XP(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.command()
    async def xp(self, ctx: aoi.AoiContext):
        await self.bot.db.ensure_xp_entry(ctx.message)
        xp = self.bot.db.xp[ctx.guild.id][ctx.author.id]
        l, x = _level(xp)
        await ctx.send_info(f"XP: {xp}  Level: {l}  {x%_xp_per_level(l+1)}")

    @commands.is_owner()
    @commands.command(
        brief="Flush XP to database manually"
    )
    async def flushxp(self, ctx: aoi.AoiContext):
        await self.bot.db.cache_flush()


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(XP(bot))
