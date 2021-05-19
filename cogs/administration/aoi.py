import os
import subprocess
from datetime import datetime
from typing import List, Dict

import aiohttp
import aiosqlite
import psutil
import redis

import aoi
import discord
from discord.ext import commands, tasks
from libs.conversions import dhm_notation, hms_notation, maybe_pluralize, sql_trim


class Bot(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.mem: int = 0
        self.max_mem: int = 0
        self.resource_loop.start()
        self.shard_loop.start()
        self.shard_counts_loop.start()
        self.redis_loop.start()
        self.ping: int = 0
        self.ping_run: List[int] = []
        self.avg_ping: int = 0
        self.shard_times: Dict[int, datetime] = {}
        self.shard_statuses: Dict[int, bool] = {}
        self.shard_server_counts: Dict[int, int] = {}
        self.redis = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

    @property
    def _config(self):
        return self.bot.config

    @property
    def description(self):
        return "Commands having to do with the bot herself"

    @tasks.loop(minutes=1)
    async def redis_loop(self):
        await self.bot.wait_until_ready()
        self.redis.set("aoi-members", sum(guild.member_count if hasattr(guild, "_member_count") else 0
                                          for guild in self.bot.guilds))
        self.redis.set("aoi-guilds", len(self.bot.guilds))

    @tasks.loop(seconds=2)
    async def resource_loop(self):
        self.mem = psutil.Process(os.getpid()).memory_info().rss // 1000000
        self.max_mem = max(self.mem, self.max_mem)
        self.ping = round(self.bot.latency * 1000)
        self.ping_run.append(self.ping)
        if len(self.ping_run) > 30 * 60:
            del self.ping_run[0]
        self.avg_ping = round(sum(self.ping_run) / len(self.ping_run))

    @resource_loop.before_loop
    async def _before_mem_loop(self):
        self.bot.logger.info("aoi:Waiting for bot")
        await self.bot.wait_until_ready()
        self.bot.logger.info("aoi:Ready!")

    @tasks.loop(seconds=1)
    async def shard_loop(self):
        if not self.bot.is_ready():
            return
        for shard in self.bot.shards:
            if shard not in self.shard_times:
                self.shard_times[shard] = datetime.now()
                self.shard_statuses[shard] = not self.bot.get_shard(shard).is_closed()
            if self.bot.get_shard(shard).is_closed() == self.shard_statuses[shard]:
                self.shard_times[shard] = datetime.now()
                self.shard_statuses[shard] = not self.bot.get_shard(shard).is_closed()

    @tasks.loop(minutes=5)
    async def shard_counts_loop(self):
        await self.bot.wait_until_ready()
        self.shard_server_counts = {}
        for guild in self.bot.guilds:
            shard_id = (guild.id >> 22) % self.bot.shard_count
            self.shard_server_counts[shard_id] = self.shard_server_counts.get(shard_id, 0) + 1

    @commands.command(
        brief="Shows bot stats"
    )
    async def stats(self, ctx: aoi.AoiContext):
        text_channels = 0
        voice_channels = 0
        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                text_channels += 1
            if isinstance(channel, discord.VoiceChannel):
                voice_channels += 1
        await ctx.embed(author=f"Aoi {self.bot.version}",
                        fields=[
                            ("Ping", f"{self.ping} ms\n"
                                     f"{self.avg_ping} ms (1h average)"),
                            ("Messages", f"{self.bot.messages}"),
                            ("Commands\nExecuted", f"{self.bot.commands_executed}"),
                            ("Uptime", dhm_notation(datetime.now() - self.bot.start_time)),
                            ("Shard", f"{self.bot.shard_id or 0}/{self.bot.shard_count}"),
                            ("Memory", f"{self.mem} MB\n"
                                       f"{self.max_mem} MB max"),
                            ("Presence", f"{len(self.bot.guilds)} Guilds\n"
                                         f"{text_channels} Text Channels\n"
                                         f"{voice_channels} Voice Channels\n"
                                         f"{len(self.bot.users)} Users Cached"),
                        ],
                        thumbnail=self.bot.user.avatar.url)

    @commands.command(brief=f"Gives a link to invite #BOT# to your server")
    async def invite(self, ctx: aoi.AoiContext):
        permissions_int = 268659776
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=" \
                     f"{permissions_int}&scope=bot"
        await ctx.send_info(f"Invite me to your server [without slash commands]({invite_url}) or "
                            f"[with slash commands]({invite_url}%20applications.commands)")

    @commands.command(
        brief="Shows #BOT#'s latency to discord"
    )
    async def ping(self, ctx: aoi.AoiContext):
        await ctx.send_info(f":ping_pong: {round(self.bot.latency * 1000)}ms")

    @commands.is_owner()
    @commands.command(
        brief="Log #BOT# out"
    )
    async def die(self, ctx: aoi.AoiContext):
        await ctx.send_ok("Bye :(")
        await self.bot.db.close()
        await self.bot.close()

    @commands.is_owner()
    @commands.command(
        brief="Flush XP/Currency to database manually"
    )
    async def flush(self, ctx: aoi.AoiContext):
        await self.bot.db.cache_flush()
        await ctx.send_ok("Cache flushed to disk")

    @commands.is_owner()
    @commands.command(
        brief="List servers the bot is part of",
        aliases=["listservers"]
    )
    async def guildlist(self, ctx: aoi.AoiContext):
        await ctx.paginate(
            [f"{g.id}\n{g.name}\n" for g in self.bot.guilds],
            title=f"Servers {self.bot.user.name if self.bot.user else ''} is in",
            n=5
        )

    @commands.is_owner()
    @commands.command(
        brief="Basic information about a server the bot is on",
    )
    async def guildinfo(self, ctx: aoi.AoiContext, guild: int):
        guild: discord.Guild = self.bot.get_guild(guild)
        if not guild:
            return await ctx.send_error("I'm not in a guild with that ID")
        created = guild.created_at.strftime("%c")
        voice_channels = len(guild.voice_channels)
        text_channels = len(guild.text_channels)
        roles = len(guild.roles) - 1
        statuses = {
            "dnd": 0,
            "idle": 0,
            "online": 0,
            "bot": 0,
            "offline": 0
        }
        m: discord.Member
        for m in guild.members:
            if m.bot:
                statuses["bot"] += 1
            else:
                statuses[str(m.status)] += 1
        await ctx.embed(
            title=f"Info for {guild}",
            fields=[
                ("ID", guild.id),
                ("Created at", created),
                ("Channels", f"{voice_channels} Voice, {text_channels} Text"),
                ("Owner", guild.owner),
                ("Members", guild.member_count),
                ("Roles", roles),
                ("Region", guild.region),
                ("Features", "\n".join(guild.features) if guild.features else "None"),
                ("Breakdown", f":green_circle: {statuses['online']} online\n"
                              f":yellow_circle: {statuses['idle']} idle\n"
                              f":red_circle: {statuses['dnd']} dnd\n"
                              f":white_circle: {statuses['offline']} offline\n"
                              f":robot: {statuses['bot']} bots\n")
            ],
            thumbnail=(guild.icon.url if guild.icon else None)
        )

    @commands.is_owner()
    @commands.command(brief="Show most used commands")
    async def commandstats(self, ctx: aoi.AoiContext):
        await ctx.embed(
            description="\n".join(
                [f"**{a[0]}**: {a[1]} usages" for a in sorted(self.bot.commands_ran.items(), key=lambda x: -x[1])[:10]]
            ),
            not_inline=list(range(10))
        )

    @commands.is_owner()
    @commands.command(brief="Sets #BOT#'s avatar", aliases=["setav"])
    async def setavatar(self, ctx: aoi.AoiContext, *, url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url) as resp:
                    await self.bot.user.edit(avatar=await resp.read())
            await ctx.send_ok("Avatar set!")
        except discord.InvalidArgument:
            return await ctx.send_error("URL must be a direct image link.")
        except discord.HTTPException as e:
            return await ctx.send_error(f"An error occurred while setting my avatar: {e}")

    @commands.is_owner()
    @commands.command(brief="Sets #BOT#'s name", aliases=["newname"])
    async def setname(self, ctx: aoi.AoiContext, *, name: str):
        if len(name) < 2 or len(name) > 32:
            return await ctx.send_error("Username must be between 2 and 32 characters")
        if any(substr in name for substr in ["@", "#", ":", "```"]):
            return await ctx.send_error("Usernames cannot contain @, #, \\`\\`\\`, or :")
        if name in ["discordtag", "everyone", "here"]:
            return await ctx.send_error("Usernames cannot be `discordtag`, `everyone`, or `here`")
        try:
            await self.bot.user.edit(username=name)
            await ctx.send_ok("Username set!")
        except discord.HTTPException as e:
            return await ctx.send_error(f"An error occurred while setting my name: {e}")

    @commands.command(brief="Shows shard stats")
    async def shards(self, ctx: aoi.AoiContext):
        # collect shard data
        closed = 0
        for shard in self.shard_statuses:
            if not self.shard_statuses[shard]:
                closed += 1
        await ctx.paginate(
            [f"Shard **{shard}**: **{round(self.bot.get_shard(shard).latency * 1000)}ms** - "
             f"**{'Connected' if self.shard_statuses[shard] else 'Disconnected'}** for "
             f"**{hms_notation(datetime.now() - self.shard_times[shard])}** - "
             f"{maybe_pluralize(self.shard_server_counts[shard], 'server', 'servers', number_format='**%i** ')}"
             for shard in self.bot.shards],
            30,
            f"{self.bot.shard_count - closed}/{self.bot.shard_count} shards online"
        )

    @commands.is_owner()
    @commands.command(brief="Update Aoi from Github")
    async def update(self, ctx: aoi.AoiContext):
        process = subprocess.Popen(["git", "pull", "--recurse-submodules"], stdout=subprocess.PIPE)
        output = process.communicate()[0]
        await ctx.send(f"Output: ```{str(output[:1800], 'utf-8')}```")
        process = subprocess.Popen(["git", "describe", "--tags"], stdout=subprocess.PIPE)
        output = process.communicate()[0]
        await ctx.send(f"Updated to {str(output, 'utf-8')}")

    @commands.is_owner()
    @commands.command(brief="Restart Aoi")
    async def restart(self, ctx: aoi.AoiContext):
        self.bot.is_restarting = True
        self.bot.restart_response_channel = ctx.channel.id
        await self.bot.db.cache_flush()
        await ctx.send_ok("Attempting to restart. See you on the other side!")
        await self.bot.close()

    @commands.is_owner()
    @commands.command(brief="Reload a shard - **Might have strange side effects**")
    async def reloadshard(self, ctx: aoi.AoiContext, shard: int):
        if shard < 0 or shard >= self.bot.shard_count:
            return await ctx.send_error(f"{shard} is an invalid shard number")
        await ctx.send_ok(f"Attempting to reload shard {shard}...")
        self.bot.status_loop.stop()
        await self.bot.get_shard(shard).reconnect()
        await ctx.send_ok(f"Shard {shard} reloaded")

    @commands.command(brief="Shows the list of placeholders")
    async def placeholders(self, ctx: aoi.AoiContext):
        await ctx.send_info(self.bot.placeholders.replace(
            ctx,
            "\n" +
            "\n".join(f"`&\u200b{p};` - &{p};" for p in self.bot.placeholders.supported)
        ))

    @commands.is_owner()
    @commands.command(brief="Runs an SQL command")
    async def sqlexec(self, ctx: aoi.AoiContext, *, sql):
        sql = sql_trim(sql)
        await ctx.embed(description=f"```sql\n{sql}\n```", footer="Type yes to run or cancel")
        resp = await ctx.input(str, ch=lambda m: m.lower() in ("cancel", "yes"))
        if resp == "yes":
            try:
                await self.bot.db.conn.executescript(sql)
                await self.bot.db.conn.commit()
                await ctx.send_ok("Executed successfully")
            except (aiosqlite.Error, aiosqlite.Warning) as e:
                await ctx.send_error(f"An error occurred while running the SQL command. If this was a complex "
                                     f"statement, it may have been partially executed.\n```{e}```")
            finally:
                await self.bot.db.conn.commit()

    @commands.is_owner()
    @commands.command(brief="Runs an SQL select command")
    async def sqlselect(self, ctx: aoi.AoiContext, *, sql: str):
        sql = sql_trim(sql)
        try:
            # TODO this breaks ```sql formatted code blocks... :thonk:... maybe remove a beginning `select`?
            rows = await self.bot.db.conn.execute_fetchall(f"select {sql}")
            await self.bot.db.conn.commit()
            await ctx.paginate(["|".join(map(str, row)) for row in rows] if rows else ["None"], 20, sql)
        except (aiosqlite.Error, aiosqlite.Warning) as e:
            await ctx.send_error(f"An error occurred while running the SQL command. If this was a complex "
                                 f"statement, it may have been partially executed.\n```{e}```")
        finally:
            await self.bot.db.conn.commit()

    @commands.is_owner()
    @commands.command(brief="View bot-wide configs")
    async def botconfig(self, ctx: aoi.AoiContext, key: str = None, value: str = None):  # noqa c901
        if not key:
            return await ctx.embed(
                title="Bot config categories",
                description=(
                        f"Do `{ctx.clean_prefix}botconfig category` to view the configs for a category\n" +
                        "\n".join(f"⋄ {cat}" for cat in self._config.yaml)
                )
            )
        if "." not in key:
            key = key.lower()
            try:
                return await ctx.embed(
                    title=f"Bot configs for {key}",
                    description=(
                            f"Do `{ctx.clean_prefix}botconfig category config_name config_value` to set a bot config\n" +  # noqa e501
                            "\n".join(f"⋄ **{key}.{k}**: {v}" for k, v in self._config.all_keys_in(key))
                    )
                )
            except ValueError:
                return await ctx.send_error(f"**{key}** is an invalid category. Do `{ctx.clean_prefix}botconfig` to "
                                            f"view the valid categories.")
        if not value:
            key = key.lower()
            try:
                return await ctx.send_info(f"**{key}** is set to {self._config.get(key)}")
            except ValueError:
                if key.split(".")[0] not in self._config.yaml:
                    return await ctx.send_error(
                        f"**{key}** is an invalid category. Do `{ctx.clean_prefix}botconfig` to "
                        f"view the valid categories.")
                else:
                    return await ctx.send_error(f"**{key}** is an invalid key. Do `{ctx.clean_prefix}botconfig "
                                                f"{key.split('.')[0]}` to view valid keys in that category")
        key = key.lower()
        try:
            previous = self._config.get(key)
        except ValueError:
            if key.split(".")[0] not in self._config.yaml:
                return await ctx.send_error(f"**{key}** is an invalid category. Do `{ctx.clean_prefix}botconfig` to "
                                            f"view the valid categories.")
            else:
                return await ctx.send_error(f"**{key}** is an invalid key. Do `{ctx.clean_prefix}botconfig "
                                            f"{key.split('.')[0]}` to view valid keys in that category")
        try:
            self._config.set(key, value)
            return await ctx.send_info(f"**{key}** was changed to `{self._config.get(key)}`"
                                       f"from `{previous}`")
        except ValueError:
            return await ctx.send_error(f"An error was raised setting the key")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Bot(bot))
