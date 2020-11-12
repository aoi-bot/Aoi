import aoi
from .base import Game

class TicTacToe(Game):
    def __init__(self, ctx: aoi.AoiContext):
        super().__init__(ctx)

    async def play(self):
        await self.ctx.send_ok("e")
