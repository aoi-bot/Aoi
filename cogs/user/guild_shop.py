import discord
from discord.ext import commands
import aoi
from libs.currency_classes import CurrencyLock


class ServerShop(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.command(
        brief="Pay someone server currency."
    )
    async def pay(self, ctx: aoi.AoiContext, member: discord.Member, amount: int):
        async with CurrencyLock(ctx, amount, False, f"Paid ${amount} to {member}"):
            await self.bot.db.ensure_guild_currency_entry(member)
            await self.bot.db.award_guild_currency(member, amount)



def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(ServerShop(bot))
