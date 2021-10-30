import typing

import tanjun

from aoi.libs.conversions import discord_number_emojis as dne


class Game:
    def __init__(
        self,
        ctx: typing.Union[tanjun.abc.SlashContext, tanjun.abc.MessageContext],
    ):
        self.ctx = ctx

    async def play(self):
        raise NotImplementedError()

    def score(self, aoi_score: int, player_score: int):
        return (
            f":person_red_hair: {dne(player_score)}\n"
            f"<:aoi:760338479841935372> {dne(aoi_score)}\n"
        )
