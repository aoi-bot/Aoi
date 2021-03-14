import asyncio
import random
from typing import Tuple

import aoi
import discord
from libs.conversions import discord_number_emojis
from .base import Game


def _xo(num, neg=False):
    return [":x:", None, ":o:"][num + 1] if not neg else \
        [":regional_indicator_x:", None, ":regional_indicator_o:"][num + 1]


def _board_pos(x: int) -> Tuple[int, int]:
    return (x - 1) // 3, (x - 1) % 3


class TicTacToe(Game):
    def __init__(self, ctx: aoi.AoiContext):
        super().__init__(ctx)

    async def play(self):  # noqa C901
        board = [[0] * 3 for _ in range(3)]

        def _get_board():
            s = "_ _\n"
            for i in range(1, 10):
                row, col = _board_pos(i)
                cur = board[row][col]
                s += discord_number_emojis(i)
                if col == 2:
                    s += "\n"
            return s

        def _status():
            wins = [
                [4, 5, 6],
                [1, 2, 3],
                [7, 8, 9],
                [8, 5, 2],
                [9, 6, 3],
                [7, 5, 3],
                [9, 5, 1],
                [7, 4, 1]
            ]
            for i in [-1, 1]:
                for row in wins:
                    if all([board[_board_pos(j)[0]][_board_pos(j)[1]] == i for j in row]):
                        return i, row
            for row in board:
                for col in row:
                    if col == 0:
                        return 0, []
            return 2, []

        def _make_next():
            # make winning move
            for i in range(1, 10):
                orig = board[_board_pos(i)[0]][_board_pos(i)[1]]
                if orig != 0:
                    continue
                board[_board_pos(i)[0]][_board_pos(i)[1]] = -1
                if _status()[0] == -1:
                    board[_board_pos(i)[0]][_board_pos(i)[1]] = -1
                    return
                board[_board_pos(i)[0]][_board_pos(i)[1]] = orig

            # block player's winning move
            for i in range(1, 10):
                orig = board[_board_pos(i)[0]][_board_pos(i)[1]]
                if orig != 0:
                    continue
                board[_board_pos(i)[0]][_board_pos(i)[1]] = 1
                if _status()[0] == 1:
                    board[_board_pos(i)[0]][_board_pos(i)[1]] = -1
                    return
                board[_board_pos(i)[0]][_board_pos(i)[1]] = orig

            # pick a random square
            sq = random.choice(list(filter(lambda i: board[_board_pos(i)[0]][_board_pos(i)[1]] == 0, list(range(0, 9)))))
            board[_board_pos(sq)[0]][_board_pos(sq)[1]] = -1

        comp = (random.random() > 0.5)

        msg = await self.ctx.embed(title="Type 1-9", description=_get_board())

        while True:
            api_board = ""
            for i in board:
                for r in i:
                    api_board += "x-o"[r+1]
            if not comp:
                await msg.edit(embed=discord.Embed(title="Your turn!",
                                                   description=None, colour=discord.Colour.blue())
                               .set_image(url=f"https://api.aoibot.xyz/tictactoe?board={api_board}"))
                sq = await self.ctx.input(int, ch=lambda x: (0 < x < 10) and board[_board_pos(x)[0]][_board_pos(
                    x)[1]] == 0,
                                          del_response=True)
                board[_board_pos(sq)[0]][_board_pos(sq)[1]] = 1
                if _status()[0] != 0:
                    break
            else:
                await msg.edit(embed=discord.Embed(title="My turn!",
                                                   description=None, colour=discord.Colour.gold())
                               .set_image(url=f"https://api.aoibot.xyz/tictactoe?board={api_board}"))
                async with self.ctx.typing():
                    await asyncio.sleep(1)
                _make_next()
                if _status()[0] != 0:
                    break
            comp = not comp

        winner, win = _status()
        s = "_ _\n"
        for i in range(1, 10):
            row, col = _board_pos(i)
            cur = board[row][col]
            s += (_xo(cur, neg=(i in win)) if cur else ":black_large_square:")
            if col == 2:
                s += "\n"
        for i in board:
            for r in i:
                api_board += "x-o"[r+1]

        if winner == 1:
            title = "You win!"
            color = discord.Colour.green()
        elif winner == -1:
            title = "You Lose ):"
            color = discord.Colour.red()
        else:
            title = "It's a tie"
            color = discord.Colour.purple()

        await msg.edit(embed=discord.Embed(title=title,
                                           description=None, colour=color)
                       .set_image(url=f"https://api.aoibot.xyz/tictactoe?board={api_board}"))
