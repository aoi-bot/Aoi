from typing import Awaitable, Callable

import discord


class Trigger:
    def __init__(self, coro: Callable[[discord.Member], Awaitable[None]]):
        self.coro = coro

    async def run(self, member: discord.Member):
        await self.coro(member)
