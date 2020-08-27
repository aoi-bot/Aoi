import discord
from discord.ext import commands
import aoi
import random


class Gambling(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Gambling :)"

    @commands.command(
        brief="Flip a coin, with an optional bet",
        aliases=["cf"]
    )
    async def coinflip(self, ctx: aoi.AoiContext, bet: int = 0, h_or_t: str = "h"):
        ht = random.choice(["heads", "tails"])
        if not bet:
            return await ctx.send_info(f"You got **{ht}**")
        if h_or_t.lower() not in "heads tails h t".split(" "):
            return await ctx.send_error("Must specify heads or tails")
        if bet > await self.bot.db.get_guild_currency(ctx.author):
            return await ctx.send_error("You don't have enough currency.")
        if bet < 5:
            return await ctx.send_error("You must bet at least 5.")
        await ctx.send_info(f"You got **{ht}**. You {'win' if ht[0] == h_or_t.lower()[0] else 'lose'} ${bet:,}")
        await self.bot.db.award_guild_currency(ctx.author, bet if ht[0] == h_or_t.lower()[0] else -bet)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Gambling(bot))
