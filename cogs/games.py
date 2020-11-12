from typing import List, Dict

import discord
from discord.ext import commands
import aoi
from games import Game, TicTacToe
from games.rps import RPS

class Minigames(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self) -> str:
        return "Minigames to play with Aoi or others"

    @commands.command(brief="Tic Tac Toe")
    async def tictactoe(self, ctx: aoi.AoiContext):
        await TicTacToe(ctx).play()

    @commands.command(brief="Tic Tac Toe")
    async def rps(self, ctx: aoi.AoiContext, turns: int = 3):
        if turns < 1 or turns > 10:
            await ctx.send_error("Number of turns must be between 1 and 10")
        await RPS(ctx, turns).play()




def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Minigames(bot))