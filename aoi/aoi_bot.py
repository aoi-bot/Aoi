from typing import Optional

import discord
from discord.ext import commands
import logging

from .custom_context import AoiContext
from .database import AoiDatabase

class AoiBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(AoiBot, self).__init__(*args, **kwargs)
        self.db: Optional[AoiDatabase] = None

    async def on_message(self, message: discord.Message):
        ctx = await self.get_context(message, cls=AoiContext)
        await self.invoke(ctx)

    async def start(self, *args, **kwargs):
        """|coro|
        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        Raises
        -------
        TypeError
            An unexpected keyword argument was received.
        """
        bot = kwargs.pop('bot', True)
        reconnect = kwargs.pop('reconnect', True)
        self.db = AoiDatabase()
        await self.db.load()

        if kwargs:
            raise TypeError("unexpected keyword argument(s) %s" % list(kwargs.keys()))

        await self.login(*args, bot=bot)
        await self.connect(reconnect=reconnect)
