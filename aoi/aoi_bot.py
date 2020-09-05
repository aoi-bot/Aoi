import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Optional, List, Union

import aiohttp.client_exceptions
import discord
import pixivapi
from discord.ext import commands

import aoi
from wrappers import gmaps as gmaps, imgur
from .custom_context import AoiContext
from .database import AoiDatabase


class AoiBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(AoiBot, self).__init__(*args, **kwargs)
        self.db: Optional[AoiDatabase] = None
        self.prefixes: Dict[int, str] = {}
        self.banned_tags: List[str] = []
        self.banned_pixiv_tags: List[str] = []
        self.gelbooru_key: str = ""
        self.gelbooru_user: str = ""
        self.weather_gov: str = ""
        self.google: str = ""
        self.nasa: str = ""
        self.accuweather: str = ""
        self.gmap: Optional[gmaps.GeoLocation] = None
        self.imgur_user: str = ""
        self.imgur_secret: str = ""
        self.pixiv_user: str = ""
        self.pixiv_password: str = ""
        self.pixiv = pixivapi.Client()
        self.imgur: Optional[imgur.Imgur] = None
        self.messages = 0
        self.commands_executed = 0
        self.start_time = datetime.now()
        self.cog_groups = {}
        self.version = "+".join(subprocess.check_output(["git", "describe", "--tags"]).
                                strip().decode("utf-8").split("-")[:-1])

        async def increment_command_count(ctx):
            self.commands_executed += 1

        self.add_listener(
            increment_command_count,
            "on_command_completion"
        )

    async def on_message(self, message: discord.Message):
        ctx: aoi.AoiContext = await self.get_context(message, cls=AoiContext)
        await self.invoke(ctx)
        if not ctx.command and not message.author.bot:
            await self.db.ensure_xp_entry(message)
            await self.db.add_xp(message)
            await self.db.add_global_currency(message)
            self.messages += 1

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
        self.db = AoiDatabase(self)
        self.banned_tags = os.getenv("BANNED_TAGS").split(",")
        self.banned_pixiv_tags = os.getenv("BANNED_TAGS").split(",") + os.getenv("BANNED_PIXIV_TAGS").split(",")
        self.gelbooru_user = os.getenv("GELBOORU_USER")
        self.gelbooru_key = os.getenv("GELBOORU_API_KEY")
        self.weather_gov = os.getenv("WEATHER_GOV_API")
        self.google = os.getenv("GOOGLE_API_KEY")
        self.nasa = os.getenv("NASA")
        self.accuweather = os.getenv("ACCUWEATHER")
        self.imgur_user = os.getenv("IMGUR")
        self.imgur_secret = os.getenv("IMGUR_SECRET")
        self.gmap = gmaps.GeoLocation(self.google)
        self.imgur = imgur.Imgur(self.imgur_user)
        self.pixiv_user = os.getenv("PIXIV")
        self.pixiv_password = os.getenv("PIXIV_PASSWORD")
        self.pixiv.login(self.pixiv_user, self.pixiv_password)
        await self.db.load()

        if kwargs:
            raise TypeError("unexpected keyword argument(s) %s" % list(kwargs.keys()))

        for i in range(0, 6):
            try:
                await self.login(*args, bot=bot)
                break
            except aiohttp.client_exceptions.ClientConnectionError as e:
                logging.warning(f"bot:Connection {i}/6 failed")
                logging.warning(f"bot:  {e}")
                logging.warning(f"bot: waiting {2 ** (i + 1)} seconds")
                await asyncio.sleep(2 ** (i + 1))
                logging.info("bot:attempting to reconnect")
        else:
            logging.error("bot: FATAL failed after 6 attempts")
            return

        for cog in self.cogs:
            cog = self.get_cog(cog)
            if not cog.description:
                logging.error(f"bot:cog {cog} has no description")
                return

        await self.connect(reconnect=reconnect)

    def find_cog(self, name: str, *,
                 allow_ambiguous=False,
                 allow_none=False,
                 check_description=False) -> Union[List[str], str]:
        found = []
        for c in self.cogs:
            if c.lower().startswith(name.lower()):
                found.append(c)
            if c.lower() == name.lower():
                found = [c]
                break
        if not found and not allow_none:
            raise commands.BadArgument(f"Module {name} not found.")
        if len(found) > 1 and not allow_ambiguous:
            raise commands.BadArgument(f"Name {name} can refer to multiple modules: "
                                       f"{', '.join(found)}. Use a more specific name.")
        return found

    def set_cog_group(self, cog: str, group: str):
        if group not in self.cog_groups:
            self.cog_groups[group] = [cog]
        else:
            self.cog_groups[group].append(cog)
