from typing import Dict, Optional, List, Union

import discord
from discord.ext import commands
import logging
import os

from .custom_context import AoiContext
from .database import AoiDatabase


class AoiBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(AoiBot, self).__init__(*args, **kwargs)
        self.db: Optional[AoiDatabase] = None
        self.prefixes: Dict[int, str] = {}
        self.banned_tags: List[str] = []
        self.gelbooru_key: str = ""
        self.gelbooru_user: str = ""

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
        self.banned_tags = os.getenv("BANNED_TAGS").split(",")
        self.gelbooru_user = os.getenv("GELBOORU_USER")
        self.gelbooru_key = os.getenv("GELBOORU_API_KEY")
        await self.db.load()

        if kwargs:
            raise TypeError("unexpected keyword argument(s) %s" % list(kwargs.keys()))

        await self.login(*args, bot=bot)
        await self.connect(reconnect=reconnect)

    def find_cog(self, name: str, *,
                 allow_ambiguous=False,
                 allow_none=False) -> Union[List[str], str]:
        found = []
        for c in self.cogs:
            if c.lower().startswith(name.lower()):
                found.append(c)
        if not found and not allow_none:
            raise commands.BadArgument(f"Module {name} not found.")
        if len(found) > 1 and not allow_ambiguous:
            raise commands.BadArgument(f"Name {name} can refer to multiple modules: "
                                       f"{', '.join(found)}. Use a more specific name.")
        return found
