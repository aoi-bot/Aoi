from typing import Optional

import discord
from discord.ext import commands
import aoi


class Currency(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands dealing with currency"

    @commands.is_owner()
    @commands.command(
        brief="Give or take currency globally"
    )
    async def award_g(self, ctx: aoi.AoiContext, member: Optional[discord.Member], amount: int):
        member = member or ctx.author
        await self.bot.db.add_global_currency(member, amount)
        await ctx.send_info(f"Added ${amount} to {member.mention}. Their new total is "
                            f"{await self.bot.db.get_global_currency(member)}.")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Currency(bot))
