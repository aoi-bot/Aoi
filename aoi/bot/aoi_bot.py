from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import subprocess
from datetime import datetime, timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import aiohttp.client_exceptions
import discord
import ksoftapi

# import pixivapi
from discord.ext import commands, tasks
from ruamel.yaml import YAML

from .. import bot
from ..wrappers import imgur

from .cmds_gen import generate
from .config import ConfigHandler
from .database import AoiDatabase

if TYPE_CHECKING:
    from aoi.bot import AoiContext


class FakeUser(discord.User):
    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)
        self.name = ""


class PlaceholderManager:
    # update complexity/context/placeholders.json when this is updated
    def user_name(self, ctx: Union[bot.AoiContext, discord.Member]) -> str:  # noqa
        return ctx.author.name if isinstance(ctx, bot.AoiContext) else ctx.name

    def user_discrim(self, ctx: Union[bot.AoiContext, discord.Member]) -> str:  # noqa
        return (
            ctx.author.discriminator
            if isinstance(ctx, bot.AoiContext)
            else ctx.discriminator
        )

    def user_mention(self, ctx: Union[bot.AoiContext, discord.Member]) -> str:  # noqa
        return ctx.author.mention if isinstance(ctx, bot.AoiContext) else ctx.mention

    def user_avatar(self, ctx: Union[bot.AoiContext, discord.Member]) -> str:  # noqa
        return str(
            ctx.author.avatar.url if isinstance(ctx, bot.AoiContext) else ctx.avatar.url
        )

    def user_tag(self, ctx: Union[bot.AoiContext, discord.Member]) -> str:  # noqa
        return str(ctx.author if isinstance(ctx, bot.AoiContext) else ctx)

    def user_id(self, ctx: Union[bot.AoiContext, discord.Member]) -> str:  # noqa
        return str(ctx.author.id if isinstance(ctx, bot.AoiContext) else ctx.id)

    def guild_name(self, ctx: AoiContext) -> str:  # noqa
        return ctx.guild.name

    def guild_icon(self, ctx: Union[bot.AoiContext, discord.Member]) -> str:  # noqa
        return str(ctx.guild.icon.url if ctx.guild.icon else None)

    @property
    def supported(self) -> List[str]:
        return list(
            filter(
                lambda x: not x.startswith("_")
                and x not in ["supported", "replace", "dict"],
                self.__class__.__dict__.keys(),
            )
        )

    def replace(self, ctx: Union[bot.AoiContext, discord.Member], msg: str) -> str:
        repl = {f"&{k};": self.__class__.__dict__[k](self, ctx) for k in self.supported}
        pattern = re.compile("|".join([re.escape(k) for k in repl.keys()]), re.M)
        return pattern.sub(lambda match: repl[match.group(0)], msg)


class AoiBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super(AoiBot, self).__init__(*args, **kwargs)
        self.shutting_down = False
        self.TRACE = 7
        for logger in [
            "aoi",
            "discord.client",
            "discord.gateway",
            "discord.http",
            "discord.ext.commands.core",
        ]:
            logging.getLogger(logger).setLevel(
                logging.DEBUG if logger == "aoi" else logging.INFO
            )
            logging.getLogger(logger).addHandler(bot.LoggingHandler())
        self.logger = logging.getLogger("aoi")
        self.config = ConfigHandler()
        self.db: Optional[AoiDatabase] = None
        self.prefixes: Dict[int, str] = {}
        self.banned_tags: List[str] = []
        self.gelbooru_key: str = ""
        self.gelbooru_user: str = ""
        self.weather_gov: str = ""
        self.google: str = ""
        self.nasa: str = ""
        self.ksoft_api: str = ""
        self.accuweather: str = ""
        self.gmap: Optional[gmaps.GeoLocation] = None
        self.imgur_user: str = ""
        self.imgur_secret: str = ""
        # self.pixiv = pixivapi.Client()
        self.imgur: Optional[imgur.Imgur] = None
        self.messages = 0
        self.commands_executed = 0
        self.start_time = datetime.now()
        self.cog_groups = {}
        version = (
            subprocess.check_output(["git", "describe", "--tags"])
            .strip()
            .decode("utf-8")
            .split("-")
        )
        self.version = "+".join(version[:-1]) if len(version) > 2 else version[0]
        self.logger.debug(f"Found version string {version}")
        self.placeholders = PlaceholderManager()
        self.tasks: Dict[discord.Member, List[bot.AoiTask]] = {}
        self.commands_ran = {}
        self.ksoft: Optional[ksoftapi.Client] = None
        self.fetched_users: Dict[int, Tuple[discord.User, datetime]] = {}
        self.is_restarting = False
        self.thumbnails: List[str] = []
        self.twitter_bearer = ""
        self.slowmodes: Dict[int, int] = {}
        self.patreon_id: str = os.getenv("PATREON_ID")
        self.patreon_secret: str = os.getenv("PATREON_SECRET")
        self.aliases: Dict[int, Dict[str, Tuple[str, bool]]] = {}

        async def command_ran(ctx: bot.AoiContext):
            self.commands_executed += 1
            if ctx.command.qualified_name not in self.commands_ran:
                self.commands_ran[ctx.command.qualified_name] = 1
            else:
                self.commands_ran[ctx.command.qualified_name] += 1

        async def on_ready():
            self.logger.info(f"Aoi {self.version} online!")
            await self.change_presence(
                activity=discord.Game(f",help | {len(self.guilds)} servers")
            )
            self.status_loop.start()
            await self.load_thumbnails()

        self.add_listener(command_ran, "on_command_completion")

        self.add_listener(on_ready, "on_ready")

    async def fetch_unknown_user(self, user_id: int) -> discord.User:
        if self.get_user(user_id):
            if user_id in self.fetched_users:
                del self.fetched_users[user_id]
            return self.get_user(user_id)
        if user_id in self.fetched_users:
            if (datetime.now() - self.fetched_users[user_id][1]).seconds > 3600:
                del self.fetched_users[user_id]
        self.fetched_users[user_id] = (await self.fetch_user(user_id), datetime.now())
        return self.fetched_users[user_id][0]

    @tasks.loop(minutes=20)
    async def status_loop(self):
        await self.change_presence(
            activity=discord.Game(
                f",help | {len(self.guilds)} servers | New support server in ,help"
            )
        )

    def create_task(
        self,
        ctx: commands.Context,
        coro: Awaitable[Any],  # noqa
        status: Optional[Callable[[], str]] = None,
    ):
        task: asyncio.Task = asyncio.create_task(coro)
        if ctx.author not in self.tasks:
            self.tasks[ctx.author] = []
        aoi_task = bot.AoiTask(task, ctx, status=status or (lambda: ""))
        self.tasks[ctx.author].append(aoi_task)
        task.add_done_callback(lambda x: self.tasks[ctx.author].remove(aoi_task))
        return task

    async def on_message(self, message: discord.Message):
        # check slowmode before all else
        if await self.check_slowmode(message):
            return

        if not message.guild:
            return

        # handle aliases and transform message if needed
        message = await self.handle_aliases(message)

        ctx: bot.AoiContext = await self.get_context(message, cls=bot.AoiContext)
        await self.invoke(ctx)
        if not ctx.command and not message.author.bot and message.guild:
            await self.db.ensure_xp_entry(message)
            await self.db.add_xp(message)
            await self.db.add_global_currency(message)
            self.messages += 1

    async def start(self, *args, **kwargs):  # noqa: C901
        """|coro|
        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        Raises
        -------
        TypeError
            An unexpected keyword argument was received.
        """

        bot = kwargs.pop("bot", True)  # noqa f841
        reconnect = kwargs.pop("reconnect", True)
        self.db = AoiDatabase(self)
        self.banned_tags = os.getenv("BANNED_TAGS").split(",")
        self.gelbooru_user = os.getenv("GELBOORU_USER")
        self.gelbooru_key = os.getenv("GELBOORU_API_KEY")
        self.weather_gov = os.getenv("WEATHER_GOV_API")
        self.google = os.getenv("GOOGLE_API_KEY")
        self.nasa = os.getenv("NASA")
        self.accuweather = os.getenv("ACCUWEATHER")
        self.imgur_user = os.getenv("IMGUR")
        self.imgur_secret = os.getenv("IMGUR_SECRET")
        self.gmap = gmaps.GeoLocation(self.google)
        self.ksoft_api = os.getenv("KSOFT")
        self.twitter_bearer = os.getenv("TWITTER_BEARER")

        # self.pixiv.login(self.pixiv_user, self.pixiv_password)
        self.imgur = imgur.Imgur(self.imgur_user)
        await self.db.load()

        self.logger.info("Loading alias table")
        for row in await self.db.conn.execute_fetchall("select * from alias"):
            if row[0] not in self.aliases:
                self.aliases[row[0]] = {row[1]: row[2]}
            else:
                self.aliases[row[0]][row[1]] = row[2]

        self.logger.info("Loaded alias table")

        if kwargs:
            raise TypeError("unexpected keyword argument(s) %s" % list(kwargs.keys()))

        for i in range(0, 6):
            try:
                self.logger.debug(f"bot:Connecting, try {i + 1}/6")
                await self.login(*args)
                break
            except aiohttp.client_exceptions.ClientConnectionError as e:
                self.logger.warning(f"bot:Connection {i + 1}/6 failed")
                self.logger.warning(f"bot:  {e}")
                self.logger.warning(f"bot: waiting {2 ** (i + 1)} seconds")
                await asyncio.sleep(2 ** (i + 1))
                self.logger.info("bot:attempting to reconnect")
        else:
            self.logger.critical("bot: failed after 6 attempts")
            return

        for cog in self.cogs:
            cog = self.get_cog(cog)
            if (
                not cog.description
                and cog.qualified_name not in self.cog_groups["Hidden"]
            ):
                self.logger.critical(f"bot:cog {cog.qualified_name} has no description")
                return

        for row in self.cog_groups.values():
            for cog_name in row:
                if not self.get_cog(cog_name):
                    self.logger.critical(f"bot:cog {cog_name} has no matching cog")
                    return

        missing_brief = []
        for command in self.commands:
            if not command.brief:
                missing_brief.append(command)

        if missing_brief:
            self.logger.error("bot:the following commands are missing help text")
            for i in missing_brief:
                self.logger.error(f"bot: - {i.cog.qualified_name}.{i.name}")
            return

        await generate(self)

        self.ksoft = ksoftapi.Client(self.ksoft_api, loop=self.loop)

        await self.connect(reconnect=reconnect)

    def find_cog(
        self,
        name: str,
        *,
        allow_ambiguous=False,
        allow_none=False,
        check_description=False,
    ) -> Union[List[str], str]:
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
            raise commands.BadArgument(
                f"Name {name} can refer to multiple modules: "
                f"{', '.join(found)}. Use a more specific name."
            )
        return found

    def set_cog_group(self, cog: str, group: str):
        if group not in self.cog_groups:
            self.cog_groups[group] = [cog]
        else:
            self.cog_groups[group].append(cog)

    def load_extensions(self):
        with open("extensions.yaml") as fp:
            extensions = YAML().load(stream=fp)
        for grp_name in extensions:
            for path, cog_name in extensions[grp_name].items():
                try:
                    self.logger.info(f"cog:Loading {grp_name}:{cog_name} from {path}")
                    super(AoiBot, self).load_extension(f"cogs.{path}")
                except discord.ClientException as e:
                    self.logger.critical(f"An error occurred while loading {path}")
                    self.logger.critical(e.__str__().split(":")[-1].strip())
                    raise
                except commands.ExtensionFailed as e:
                    self.logger.critical(f"An error occurred while loading {path}")
                    self.logger.critical(e.__str__().split(":")[-1].strip())
                    raise
                self.set_cog_group(cog_name, grp_name)

    def random_thumbnail(self) -> str:
        return (
            random.choice(self.thumbnails) if self.thumbnails else self.user.avatar.url
        )

    async def load_thumbnails(self):
        if os.path.exists("loaders/thumbnails.txt"):
            with open("loaders/thumbnails.txt", "r") as fp:
                self.thumbnails = fp.readlines()

    def convert_json(self, msg: str):  # does not convert placeholders
        try:
            msg = json.loads(msg)
        except json.JSONDecodeError:
            msg = {"plainText": msg}
        if isinstance(msg, str):
            msg = {"plainText": msg}
        if "plainText" in msg:
            content = msg.pop("plainText")
        else:
            content = None
        if len(msg.keys()) < 2:  # no embed here:
            embed = None
        else:
            embed = msg
        return content, embed

    async def send_json_to_channel(
        self,
        channel: int,
        msg: str,
        *,
        member: discord.Member = None,
        delete_after=None,
    ):
        if member:
            msg = self.placeholders.replace(member, msg)
            if not member.guild.get_channel(channel):
                raise commands.CommandError("Channel not in server")
        try:
            msg = json.loads(msg)
        except json.JSONDecodeError:
            msg = {"plainText": msg}
        if isinstance(msg, str):
            msg = {"plainText": msg}
        if "plainText" in msg:
            content = msg.pop("plainText")
        else:
            content = None
        if len(msg.keys()) < 2:  # no embed here:
            return await self.get_channel(channel).send(
                content=content, delete_after=delete_after
            )
        thumbnail = msg.pop("thumbnail", None) if msg else None
        image = msg.pop("image", None) if msg else None
        msg["description"] = msg.get("description", "_ _")
        embed = discord.Embed.from_dict(msg)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)
        await self.get_channel(channel).send(
            content=content, embed=embed, delete_after=delete_after
        )

    async def check_slowmode(self, message: discord.Message):
        if message.channel.id not in self.slowmodes:
            return False
        if message.author.permissions_in(message.channel).manage_messages:
            return False
        duration: int = self.slowmodes[message.channel.id]
        row = await (
            await self.db.conn.execute(
                "select timestamp from last_messages where user=? and channel=?",
                (message.author.id, message.channel.id),
            )
        ).fetchone()
        last = row[0] if row else 0
        if message.created_at < datetime.fromtimestamp(last) + timedelta(
            seconds=duration
        ):
            await message.delete()
            return True
        if last:
            await self.db.conn.execute(
                "update last_messages set timestamp=? where user=? and channel=?",
                (message.created_at.timestamp(), message.author.id, message.channel.id),
            )
        else:
            await self.db.conn.execute(
                "insert into last_messages values (?,?,?)",
                (message.channel.id, message.author.id, message.created_at.timestamp()),
            )
        return False

    async def handle_aliases(self, message: discord.Message) -> discord.Message:
        content: str = message.content
        if message.guild.id not in self.aliases:
            return message

        if content.split(" ")[0] in self.aliases[message.guild.id]:
            message.content = " ".join(
                [self.aliases[message.guild.id][content.split(" ")[0]]]
                + content.split(" ")[1:]
            )
            return message
        return message

    async def rev_alias(self, ctx, command: str) -> Optional[List[Tuple[str, str]]]:
        if ctx.guild.id in self.aliases and self.aliases[ctx.guild.id]:
            return [
                (alias, to)
                for alias, to in self.aliases[ctx.guild.id].items()
                if to[0].split(" ")[0] == command
            ] or None
        return None
