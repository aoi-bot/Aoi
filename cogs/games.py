import aoi
from discord.ext import commands
from games import TicTacToe
from games.rps import RPS
from libs.currency_classes import CurrencyLock


class Minigames(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self) -> str:
        return f"Minigames to play with {self.bot.user.name if self.bot.user else ''} or others"

    @commands.command(brief="Play tic tac toe", aliases=["ttt"])
    async def tictactoe(self, ctx: aoi.AoiContext):
        await TicTacToe(ctx).play()

    @commands.command(brief="Play rock paper scissors, with an optional amount of turns",
                      flags={"bet": [int, "Amount to bet"]})
    async def rps(self, ctx: aoi.AoiContext, turns: int = 3):
        if turns < 1 or turns > 10:
            return await ctx.send_error("Number of turns must be between 1 and 10")
        if "bet" in ctx.flags and ctx.flags["bet"]:
            await self.bot.db.ensure_guild_currency_entry(ctx.author)
            bet = ctx.flags["bet"]
            if bet < 5:
                return await ctx.send_error("You must bet more than $5")
            if bet > await self.bot.db.get_guild_currency(ctx.author):
                return await ctx.send_error(f"You only have ${self.bot.db.get_guild_currency(ctx.author)}")
            await self.bot.db.award_guild_currency(ctx.author, -bet)  # hold
            try:
                res = await RPS(ctx, turns).play()
                if res == 0:
                    return await self.bot.db.award_guild_currency(ctx.author, int(1.95*bet))
                if res == 1:
                    return await self.bot.db.award_guild_currency(ctx.author, bet)
                return
            except Exception: # noqa
                return await self.bot.db.award_guild_currency(ctx.author, bet)
        else:
            await RPS(ctx, turns).play()



def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Minigames(bot))
