import os
from datetime import datetime
from typing import List

import discord
import psutil
from discord.ext import commands, tasks

import aoi
from libs.conversions import dhm_notation


class Bot(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.mem: int = 0
        self.max_mem: int = 0
        self.resource_loop.start()
        self.ping: int = 0
        self.ping_run: List[int] = []
        self.avg_ping: int = 0

    @property
    def description(self):
        return "Commands having to do with the bot herself"

    @tasks.loop(minutes=2)
    async def resource_loop(self):
        self.mem = psutil.Process(os.getpid()).memory_info().rss // 1000000
        self.max_mem = max(self.mem, self.max_mem)
        self.ping = round(self.bot.latency * 1000)
        self.ping_run.append(self.ping)
        if len(self.ping_run) > 30:
            del self.ping_run[0]
        self.avg_ping = round(sum(self.ping_run) / len(self.ping_run))

    @resource_loop.before_loop
    async def _before_mem_loop(self):
        self.bot.logger.info("aoi:Waiting for bot")
        await self.bot.wait_until_ready()
        self.bot.logger.info("aoi:Ready!")

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
                            ("Memory", f"{self.mem} MB\n"
                                       f"{self.max_mem} MB max"),
                            ("Presence", f"{len(self.bot.guilds)} Guilds\n"
                                         f"{text_channels} Text Channels\n"
                                         f"{voice_channels} Voice Channels\n"
                                         f"{len(self.bot.users)} Users Cached"),
                        ],
                        thumbnail=self.bot.user.avatar_url)

    @commands.command(brief="Gives a link to invite Aoi to your server")
    async def invite(self, ctx: aoi.AoiContext):
        permissions_int = 268659776
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=" \
                     f"{permissions_int}&scope=bot"
        await ctx.send_info(f"Invite me to your server [here]({invite_url})")

    @commands.command(
        brief="Shows Aoi's latency to discord"
    )
    async def ping(self, ctx: aoi.AoiContext):
        await ctx.send_info(f":ping_pong: {round(self.bot.latency * 1000)}ms")

    @commands.is_owner()
    @commands.command(
        brief="Log Aoi out"
    )
    async def die(self, ctx: aoi.AoiContext):
        await self.bot.db.close()
        await self.bot.logout()

    @commands.is_owner()
    @commands.command(
        brief="Flush XP/Currency to database manually"
    )
    async def flush(self, ctx: aoi.AoiContext):
        await self.bot.db.cache_flush()
        await ctx.send_ok("Cache flushed to disk")

    @commands.is_owner()
    @commands.command(
        brief="List servers the bot is part of"
    )
    async def guildlist(self, ctx: aoi.AoiContext):
        await ctx.paginate(
            [f"{g.id}\n{g.name}\n" for g in self.bot.guilds],
            title="Servers Aoi is in",
            n=5
        )

    @commands.is_owner()
    @commands.command(
        brief="Basic information about a server the bot is on",
    )
    async def guildinfo(self, ctx: aoi.AoiContext, guild: int):
        guild: discord.Guild = self.bot.get_guild(guild)
        if not guild:
            return await ctx.send_error("Im'm not in a guild with that ID")
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
            thumbnail=guild.icon_url
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


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Bot(bot))
