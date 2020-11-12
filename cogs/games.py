from typing import List, Dict

import discord
from discord.ext import commands
import aoi
from games import Game, TicTacToe

class Minigames(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self) -> str:
        return "Minigames to play with Aoi or others"

    @commands.command(brief="Tic Tac Toe")
    async def tictactoe(self, ctx: aoi.AoiContext):
        await TicTacToe(ctx).play()




def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Minigames(bot))
